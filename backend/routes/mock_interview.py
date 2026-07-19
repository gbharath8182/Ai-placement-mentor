import json
import random
import re
import uuid
from typing import Dict, Any, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.database import get_collection
from backend.auth import get_current_user
from backend.config import settings

router = APIRouter(prefix="/mock-interview", tags=["mock-interview"])

# In-memory session store: session_id -> session dict
# NOTE: resets on server restart. Fine for demo use; swap for a Mongo
# collection later if cross-restart persistence is needed.
interview_sessions: Dict[str, Dict[str, Any]] = {}

VALID_MODES = {"coding", "hr", "technical", "mixed"}
DIFFICULTY_LEVELS = ("beginner", "intermediate", "advanced")


class MockInterviewStartRequest(BaseModel):
    domain_slug: str
    mode: str = "mixed"  # coding, hr, technical, mixed
    num_questions: int = 5


class MockInterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str


class ExplainMoreRequest(BaseModel):
    session_id: str


async def call_groq(messages: list, model: str) -> str:
    """Direct Groq call parameterized by model. Kept independent from
    ai.py so mock-interview grading/generation can pick primary or
    fallback model without touching the shared ai.py used elsewhere."""
    if not settings.GROQ_API_KEY:
        return json.dumps({"_demo_mode": True, "note": "GROQ_API_KEY not configured"})

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {"model": model, "messages": messages, "temperature": 0.4, "stream": False}

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers, json=body, timeout=45.0
            )
            if r.status_code != 200:
                return f"__GROQ_ERROR__ ({r.status_code}): {r.text}"
            res = r.json()
            return res["choices"][0]["message"]["content"]
        except Exception as e:
            return f"__GROQ_ERROR__ Exception: {str(e)}"


def extract_json(text: str) -> Optional[dict]:
    try:
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        return json.loads(cleaned)
    except Exception:
        return None


async def call_groq_json_with_retry(
    messages: list, primary_model: str, fallback_model: str, force_fallback: bool = False
) -> dict:
    """Calls the primary model unless force_fallback is set. If the
    response isn't parseable JSON, automatically retries once with the
    fallback model - this is the actual escalation behavior: on failure
    OR on explicit request for deeper output."""
    model_used = fallback_model if force_fallback else primary_model
    raw = await call_groq(messages, model_used)
    parsed = extract_json(raw)

    if parsed is None and not force_fallback:
        model_used = fallback_model
        raw = await call_groq(messages, fallback_model)
        parsed = extract_json(raw)

    return {"parsed": parsed, "raw": raw, "model_used": model_used}


def _grading_rubric(mode: str) -> str:
    if mode == "hr":
        return (
            "Evaluate as a behavioral/HR interviewer. Focus on: communication clarity, "
            "self-awareness, use of concrete examples (STAR method: Situation, Task, Action, "
            "Result), initiative and innovative thinking, teamwork and collaboration signals, "
            "and overall professionalism. This is NOT technical grading - do not penalize for "
            "lack of code or algorithms."
        )
    if mode == "technical":
        return (
            "Evaluate as a senior engineering panel interviewer conducting a real, in-depth "
            "technical interview. Focus on: technical correctness, depth of reasoning, "
            "awareness of trade-offs and edge cases, ability to justify design/engineering "
            "decisions, and clarity of communication as a working engineer would need."
        )
    return (
        "Evaluate as a technical interviewer grading a coding/technical answer. Focus on: "
        "correctness, completeness, code quality or algorithmic reasoning, complexity "
        "awareness, and edge case handling."
    )


def _question_generation_prompt(mode: str, domain_doc: dict, asked_questions: List[str], difficulty: str) -> str:
    topics = [t.get("name") for t in domain_doc.get("topics", [])] if domain_doc.get("topics") else []
    skills = domain_doc.get("skills_required", [])
    avoid = "\n".join(f"- {q}" for q in asked_questions) if asked_questions else "(none yet)"

    if mode == "coding":
        focus = (
            "Generate ONE original coding interview question specific to this domain. It "
            "should be answerable by writing code or pseudocode/logic as a typed text answer "
            "(the candidate is not running code, just describing/writing it)."
        )
    elif mode == "technical":
        focus = (
            "Generate ONE in-depth technical interview question as a senior engineer would ask "
            "in a real panel interview for this domain - this can be a conceptual deep-dive, a "
            "system design question, or an engineering judgment/trade-off question. Vary the "
            "style across the interview rather than always the same type."
        )
    else:
        focus = "Generate ONE relevant behavioral or interview question for this domain."

    return (
        f"You are designing interview questions for the domain: {domain_doc.get('domain_slug')}.\n"
        f"Relevant topics: {', '.join(topics) if topics else 'general'}\n"
        f"Relevant skills: {', '.join(skills) if skills else 'general'}\n"
        f"{focus}\n"
        f"Required difficulty: {difficulty}. Make the scope and expected depth appropriate for this level.\n"
        f"Do NOT repeat or closely resemble any of these already-asked questions:\n{avoid}\n\n"
        "Respond with STRICT JSON ONLY, no markdown, no preamble, matching exactly:\n"
        '{"question": "...", "category": "coding|system_design|conceptual|judgment|hr", "difficulty": "beginner|intermediate|advanced"}'
    )


async def _get_next_question(mode: str, domain_doc: dict, session: dict) -> dict:
    """Returns {"category": ..., "question": ...}. hr/mixed pull from the
    curated static pool first; coding/technical (and pool-exhausted
    hr/mixed) generate a fresh domain-specific question via AI."""
    difficulty = DIFFICULTY_LEVELS[len(session["questions_asked"]) % len(DIFFICULTY_LEVELS)]
    if mode == "hr":
        pool = session.get("_pool")
        if pool is None:
            ip = domain_doc.get("interview_prep", {}) or {}
            pool = [{"category": "hr", "question": q} for q in (ip.get("hr_questions", []) or [])]
            random.shuffle(pool)
            session["_pool"] = pool
        idx = session["index"]
        if idx < len(pool):
            question = dict(pool[idx])
            question["difficulty"] = difficulty
            return question
        asked = [q["question"] for q in session["questions_asked"]]
        prompt = _question_generation_prompt("hr", domain_doc, asked, difficulty)
        result = await call_groq_json_with_retry(
            [{"role": "system", "content": prompt}, {"role": "user", "content": "Generate the question."}],
            settings.GROQ_PRIMARY_MODEL, settings.GROQ_FALLBACK_MODEL
        )
        parsed = result["parsed"] or {}
        question = parsed.get("question") or "Tell me about a time you solved a difficult problem."
        return {"category": "hr", "question": question, "difficulty": difficulty}

    if mode == "mixed":
        pool = session.get("_pool")
        if pool is None:
            ip = domain_doc.get("interview_prep", {}) or {}
            pool = []
            for q in ip.get("coding_questions", []) or []:
                pool.append({"category": "coding", "question": q})
            for q in ip.get("hr_questions", []) or []:
                pool.append({"category": "hr", "question": q})
            for q in ip.get("system_design_questions", []) or []:
                pool.append({"category": "system_design", "question": q})
            random.shuffle(pool)
            session["_pool"] = pool
        idx = session["index"]
        if idx < len(pool):
            question = dict(pool[idx])
            question["difficulty"] = difficulty
            return question
        # pool exhausted - fall through to AI generation below

    asked = [q["question"] for q in session["questions_asked"]]
    force_fallback = (mode == "technical")
    gen_mode = mode if mode in ("coding", "technical") else "coding"
    prompt = _question_generation_prompt(gen_mode, domain_doc, asked, difficulty)
    result = await call_groq_json_with_retry(
        [{"role": "system", "content": prompt}, {"role": "user", "content": "Generate the question."}],
        settings.GROQ_PRIMARY_MODEL, settings.GROQ_FALLBACK_MODEL,
        force_fallback=force_fallback
    )
    parsed = result["parsed"]
    if not parsed or not parsed.get("question"):
        return {
            "category": "coding",
            "question": "Explain how you would approach solving a problem in this domain, and walk through your reasoning.",
            "difficulty": difficulty,
        }
    model_difficulty = parsed.get("difficulty", difficulty)
    return {
        "category": parsed.get("category", "coding"),
        "question": parsed["question"],
        "difficulty": model_difficulty if model_difficulty in DIFFICULTY_LEVELS else difficulty,
    }


@router.post("/start")
async def start_mock_interview(req: MockInterviewStartRequest, current_user: dict = Depends(get_current_user)):
    mode = req.mode if req.mode in VALID_MODES else "mixed"

    domain_coll = get_collection("domain_details")
    domain_doc = await domain_coll.find_one({"domain_slug": req.domain_slug})
    if not domain_doc:
        # All platform domains can be practiced, even while their long-form
        # roadmap is being authored. Build a small, safe AI context from the
        # domain card and its published topics.
        domains_coll = get_collection("domains")
        domain_card = await domains_coll.find_one({"slug": req.domain_slug})
        if not domain_card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown domain")
        topics_coll = get_collection("topics")
        topic_titles = [t.get("title", "") async for t in topics_coll.find(
            {"domain_slug": req.domain_slug}, {"title": 1}
        )]
        domain_doc = {
            "domain_slug": req.domain_slug,
            "topics": [{"name": title} for title in topic_titles if title],
            "skills_required": [],
            "interview_prep": {},
            "description": domain_card.get("description", ""),
        }

    session_id = str(uuid.uuid4())
    session = {
        "user_id": str(current_user["id"]),
        "domain_slug": req.domain_slug,
        "mode": mode,
        "num_questions": max(1, min(req.num_questions, 15)),
        "index": 0,
        "questions_asked": [],
        "results": [],
        "_domain_doc": domain_doc,
    }
    interview_sessions[session_id] = session

    first_q = await _get_next_question(mode, domain_doc, session)
    session["questions_asked"].append(first_q)

    return {
        "session_id": session_id,
        "domain_slug": req.domain_slug,
        "mode": mode,
        "question_number": 1,
        "total_questions": session["num_questions"],
        "category": first_q["category"],
        "difficulty": first_q["difficulty"],
        "question": first_q["question"]
    }


@router.post("/answer")
async def submit_mock_interview_answer(req: MockInterviewAnswerRequest, current_user: dict = Depends(get_current_user)):
    session = interview_sessions.get(req.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found or has expired (server may have restarted)"
        )
    if session["user_id"] != str(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")

    idx = session["index"]
    if idx >= len(session["questions_asked"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active question for this session")

    current_q = session["questions_asked"][idx]
    mode = session["mode"]

    word_count = len(req.answer.split())
    force_fallback = (mode == "technical") or (word_count > 100)

    rubric = _grading_rubric(mode)
    system_prompt = (
        f"{rubric}\n\n"
        f"Question asked ({current_q['category']}): {current_q['question']}\n\n"
        "Grade ONLY the candidate's answer below. Respond with STRICT JSON ONLY - no markdown, "
        "no preamble - matching exactly this schema:\n"
        '{"score": <integer 0-10>, "strengths": ["...", "..."], "weaknesses": ["...", "..."], '
        '"model_answer_hint": "..."}\n'
        "score: 0 = blank or completely wrong, 10 = expert-level complete answer.\n"
        "strengths: 1-3 short bullet points (empty list if none).\n"
        "weaknesses: 1-3 short bullet points (empty list if none).\n"
        "model_answer_hint: one or two sentences on what a strong answer would include."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Candidate's answer: {req.answer}"}
    ]

    result = await call_groq_json_with_retry(
        messages, settings.GROQ_PRIMARY_MODEL, settings.GROQ_FALLBACK_MODEL, force_fallback=force_fallback
    )
    parsed = result["parsed"] or {}
    score = parsed.get("score", 0)
    try:
        score = max(0, min(10, int(score)))
    except (TypeError, ValueError):
        score = 0

    graded = {
        "score": score,
        "strengths": parsed.get("strengths", []) or [],
        "weaknesses": parsed.get("weaknesses", []) or ["Could not parse grading response - please try again."],
        "model_answer_hint": parsed.get("model_answer_hint", "") or "",
        "graded_by_model": result["model_used"]
    }

    session["results"].append({
        "question": current_q["question"],
        "category": current_q["category"],
        "difficulty": current_q.get("difficulty", "intermediate"),
        "answer": req.answer,
        **graded
    })
    session["index"] += 1

    if session["index"] < session["num_questions"]:
        next_q = await _get_next_question(mode, session["_domain_doc"], session)
        session["questions_asked"].append(next_q)
        return {
            "done": False,
            "feedback": graded,
            "question_number": session["index"] + 1,
            "total_questions": session["num_questions"],
            "category": next_q["category"],
            "difficulty": next_q["difficulty"],
            "question": next_q["question"]
        }

    scores = [r["score"] for r in session["results"]]
    average_score = round(sum(scores) / len(scores), 1) if scores else 0
    return {
        "done": True,
        "feedback": graded,
        "summary": {
            "average_score": average_score,
            "questions_answered": len(session["results"]),
            "mode": mode,
            "per_question": session["results"]
        }
    }


class EndInterviewRequest(BaseModel):
    session_id: str


@router.post("/end")
async def end_mock_interview(req: EndInterviewRequest, current_user: dict = Depends(get_current_user)):
    """Lets a candidate stop early and still get scored on whatever
    questions they already answered, instead of requiring all
    num_questions to be completed."""
    session = interview_sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found or has expired")
    if session["user_id"] != str(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")

    scores = [r["score"] for r in session["results"]]
    average_score = round(sum(scores) / len(scores), 1) if scores else 0
    return {
        "summary": {
            "average_score": average_score,
            "questions_answered": len(session["results"]),
            "mode": session["mode"],
            "per_question": session["results"]
        }
    }


@router.post("/explain-more")
async def explain_more(req: ExplainMoreRequest, current_user: dict = Depends(get_current_user)):
    """Deeper explanation of the most recently graded question. Always
    uses the fallback (120b) model, per the request that more-detailed
    output should escalate to the larger model."""
    session = interview_sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found or has expired")
    if session["user_id"] != str(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    if not session["results"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No graded question yet for this session")

    last = session["results"][-1]
    system_prompt = (
        "You are an expert interviewer giving a candidate a deeper, more detailed explanation "
        f"after grading their answer to this question: {last['question']}\n"
        f"Their answer was: {last['answer']}\n"
        f"Their score was: {last['score']}/10\n\n"
        "Provide a thorough, in-depth explanation of the ideal answer, including reasoning, "
        "edge cases, and any relevant depth the candidate's answer missed. Plain text, no JSON, "
        "a few short paragraphs."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Please give me a deeper explanation."}
    ]
    explanation = await call_groq(messages, settings.GROQ_FALLBACK_MODEL)
    return {"explanation": explanation, "model_used": settings.GROQ_FALLBACK_MODEL}
