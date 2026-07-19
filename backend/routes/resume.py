import json
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.config import settings

router = APIRouter(prefix="/resume", tags=["resume"])


class ProjectInput(BaseModel):
    title: str
    description: str
    technologies: List[str] = []
    github_url: str = ""
    live_url: str = ""


class ResumeGenerateRequest(BaseModel):
    full_name: str
    target_role: str
    experience_level: str = "fresher"  # fresher, intermediate, experienced
    skills: List[str] = []
    projects: List[ProjectInput] = []
    education: str = ""
    achievements: List[str] = []
    tone: str = "concise"  # concise, detailed
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    job_description: str = ""


async def call_groq_text(messages: list, model: str) -> str:
    if not settings.GROQ_API_KEY:
        return (
            "# [Demonstration Mode]\n\n"
            "GROQ_API_KEY is not configured in your .env file, so this is placeholder text. "
            "Add GROQ_API_KEY to enable real resume generation."
        )

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {"model": model, "messages": messages, "temperature": 0.5, "stream": False}

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers, json=body, timeout=60.0
            )
            if r.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Groq API error ({r.status_code}): {r.text}"
                )
            res = r.json()
            return res["choices"][0]["message"]["content"]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Exception connecting to Groq: {str(e)}"
            )


@router.post("/generate")
async def generate_resume(req: ResumeGenerateRequest, current_user: dict = Depends(get_current_user)):
    if not req.full_name.strip() or not req.target_role.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="full_name and target_role are required"
        )

    projects_str = "\n".join(
        f"- {p.title}: {p.description}\n  Technologies: {', '.join(p.technologies) or 'not supplied'}"
        f"\n  GitHub: {p.github_url or 'not supplied'} | Live demo: {p.live_url or 'not supplied'}"
        for p in req.projects
    ) if req.projects else "(none provided)"
    skills_str = ", ".join(req.skills) if req.skills else "(none provided)"
    achievements_str = "\n".join(f"- {a}" for a in req.achievements) if req.achievements else "(none provided)"

    tone_instruction = (
        "Keep it concise and punchy - one page worth of content, tight bullet points."
        if req.tone == "concise" else
        "Provide fuller detail on each point - this can run slightly longer than one page."
    )

    contact_line = " | ".join(filter(None, [req.email, req.phone, req.location, req.linkedin_url, req.github_url, req.portfolio_url]))
    candidate_facts = (
        f"Candidate name: {req.full_name}\nTarget role/domain: {req.target_role}\n"
        f"Experience level: {req.experience_level}\nContact details: {contact_line or '(not supplied)'}\n"
        f"Skills: {skills_str}\nProjects:\n{projects_str}\nEducation: {req.education or '(none provided)'}\n"
        f"Achievements/certifications:\n{achievements_str}\nJob description or target keywords: {req.job_description or '(not supplied)'}"
    )

    # Stage 1 uses the fast model to find an honest, candidate-specific angle.
    # Stage 2 uses the larger model to turn that plan into a polished resume.
    planner_prompt = (
        "You are a technical recruiter. Extract an honest, ATS-aware positioning plan from these candidate facts. "
        "Do not invent achievements, employers, metrics, or skills. Return concise plain text with: strongest theme, relevant keywords, and facts that need careful wording.\n\n"
        + candidate_facts
    )
    positioning = await call_groq_text(
        [{"role": "system", "content": planner_prompt}, {"role": "user", "content": "Create the positioning plan."}],
        settings.GROQ_PRIMARY_MODEL,
    )

    system_prompt = (
        "You are an expert technical resume writer helping students and early-career "
        "candidates create genuinely strong, honest, ATS-friendly resumes for real job "
        "applications. Do not invent facts, companies, numbers, or experience the candidate "
        "did not provide - only elaborate on and better phrase what they gave you.\n\n"
        f"{candidate_facts}\n\n"
        f"Recruiter positioning plan (use only when it remains supported by the facts):\n{positioning}\n\n"
        f"{tone_instruction}\n\n"
        "Output a complete resume in clean Markdown with these sections in order: "
        "# {Full Name}, a one-line contact/title line using supplied links only, ## Summary (2-3 sentences), "
        "## Skills (grouped, as a bullet or comma list), ## Projects (bullet points per "
        "project, action-verb-led, quantify impact only if the candidate's description "
        "supports it), ## Education, and ## Achievements & Certifications (omit this "
        "section entirely if none were provided). Do not add any explanation before or "
        "after the resume - output ONLY the Markdown resume itself."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Generate my resume."}
    ]

    resume_markdown = await call_groq_text(messages, settings.GROQ_FALLBACK_MODEL)
    return {
        "resume_markdown": resume_markdown,
        "models_used": [settings.GROQ_PRIMARY_MODEL, settings.GROQ_FALLBACK_MODEL],
    }
