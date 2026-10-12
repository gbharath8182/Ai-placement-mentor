import hashlib
import math
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.curriculum import load_curriculum
from backend.database import get_collection


MAX_EVIDENCE = 64
REASSESS_AFTER = timedelta(days=14)
KINDS = ("quiz", "coding", "reading")


def _identifier(value, name):
    if not isinstance(value, str) or not 1 <= len(value) <= 128 or not value.strip():
        raise ValueError(f"Invalid {name}")
    return value


def mastery_key(user_id, topic_slug):
    try:
        user_id = ObjectId(user_id)
    except (InvalidId, TypeError, ValueError):
        raise ValueError("Invalid user ID") from None
    _identifier(topic_slug, "topic slug")
    digest = hashlib.sha256(f"{user_id}\0{topic_slug}".encode("utf-8")).hexdigest()
    return {"_id": "mastery:v1:" + digest, "user_id": user_id, "topic_slug": topic_slug}


def topic_checks(topic):
    """Normalize trusted catalog quizzes, retaining answers for server grading only."""
    sections = [(None, topic)]
    sections.extend(enumerate(topic.get("subtopics") or []))
    checks = []
    seen = set()
    for subtopic_index, section in sections:
        fallback_concept = "legacy:topic" if subtopic_index is None else f"legacy:subtopic:{subtopic_index}"
        for block_index, block in enumerate(section.get("content_blocks") or []):
            if not isinstance(block, dict) or block.get("type") != "knowledge_check":
                continue
            fallback_id = (
                f"legacy:topic:block:{block_index}" if subtopic_index is None else
                f"legacy:subtopic:{subtopic_index}:block:{block_index}"
            )
            block_id = block.get("block_id") or block.get("id") or fallback_id
            concept_id = block.get("concept_id") or section.get("concept_id") or fallback_concept
            _identifier(block_id, "check ID")
            _identifier(concept_id, "concept ID")
            options = block.get("options")
            correct_index = block.get("correct_index")
            question = block.get("question")
            explanation = block.get("explanation", "")
            if (
                block_id in seen or not isinstance(question, str) or not question.strip()
                or len(question) > 8000 or not isinstance(options, list) or not 2 <= len(options) <= 20
                or any(not isinstance(option, str) or not option.strip() or len(option) > 2000 for option in options)
                or type(correct_index) is not int or not 0 <= correct_index < len(options)
                or not isinstance(explanation, str) or len(explanation) > 8000
            ):
                raise ValueError("Invalid knowledge-check content")
            seen.add(block_id)
            checks.append({
                "block_id": block_id, "concept_id": concept_id, "question": question,
                "options": list(options), "subtopic_index": subtopic_index, "block_index": block_index,
                "correct_index": correct_index, "explanation": explanation,
            })
    return checks


def public_check(check):
    return {"id": check["block_id"], **{name: check[name] for name in (
        "block_id", "concept_id", "question", "options", "subtopic_index", "block_index"
    )}}


def serialize_checks(topic):
    """Public question/options/identity whitelist; never includes answers or explanations."""
    return [public_check(check) for check in topic_checks(topic)]


async def load_topic(topic_slug):
    """Shared trusted catalog lookup, with built-in fallback only for an absent DB topic."""
    _identifier(topic_slug, "topic slug")
    topic = await get_collection("topics").find_one({"slug": topic_slug})
    if topic is not None:
        return topic
    try:
        curriculum = load_curriculum()
    except (OSError, ValueError):
        raise RuntimeError("Trusted curriculum is unavailable") from None
    return next((topic for topic in curriculum["topics"] if topic["slug"] == topic_slug), None)


def _timestamp(value):
    if not isinstance(value, datetime):
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _fresh(item, now):
    recorded_at = _timestamp(item.get("recorded_at"))
    return recorded_at is not None and -timedelta(minutes=5) <= now - recorded_at < REASSESS_AFTER


def _mean(items):
    return sum(item["score"] for item in items) / len(items) if items else None


def summarize_mastery(topic, document=None, now=None):
    """A transparent heuristic, not a calibrated probability of learning."""
    now = now or datetime.now(timezone.utc)
    checks = topic_checks(topic)
    check_map = {check["block_id"]: check for check in checks}
    policy = topic.get("mastery_policy") or {}
    if not isinstance(policy, dict):
        raise ValueError("Invalid lesson mastery policy")
    coding_required = policy.get("coding_required") is not False
    minimum_quizzes = 2 if coding_required else 3
    expected_concepts = list(dict.fromkeys(check["concept_id"] for check in checks))
    minimum_concepts = min(2, len(expected_concepts)) or 1
    latest = {}
    for item in ((document or {}).get("evidence") or [])[-MAX_EVIDENCE:]:
        if (
            not isinstance(item, dict) or item.get("kind") not in KINDS
            or not isinstance(item.get("source_id"), str)
            or type(item.get("score")) not in (int, float)
            or not math.isfinite(item["score"]) or not 0 <= item["score"] <= 100
        ):
            continue
        if item["kind"] == "quiz":
            check = check_map.get(item["source_id"])
            if check is None or item.get("concept_id") != check["concept_id"]:
                continue
        latest[(item["kind"], item["source_id"])] = item
    fresh = [item for item in latest.values() if _fresh(item, now)]
    quizzes = [item for item in fresh if item["kind"] == "quiz"]
    coding = [item for item in fresh if item["kind"] == "coding"]
    quiz_score, coding_score = _mean(quizzes), _mean(coding)
    score = ((quiz_score or 0) + (coding_score or 0)) / 2 if coding_required else (quiz_score or 0)
    concepts = []
    for concept_id in expected_concepts:
        concept_quizzes = [item for item in quizzes if item.get("concept_id") == concept_id]
        concept_coding = [item for item in coding if item.get("concept_id") == concept_id] if coding_required else []
        concept_quiz_score = _mean(concept_quizzes)
        concept_coding_score = _mean(concept_coding)
        concept_score = concept_quiz_score or 0
        if concept_coding_score is not None:
            concept_score = (concept_score + concept_coding_score) / 2
        if concept_quiz_score is None:
            concept_status = "review"
            concept_reasons = ["No fresh quiz evidence for this concept; reassess it."]
        elif concept_quiz_score < 80 or (concept_coding_score is not None and concept_coding_score < 80):
            concept_status = "weak"
            concept_reasons = ["Fresh assessment evidence is below 80 for this concept."]
        else:
            concept_status = "mastered"
            concept_reasons = ["Fresh concept quiz evidence is at least 80; this is not topic mastery."]
        concepts.append({
            "concept_id": concept_id, "score": round(concept_score, 2), "quiz_score": concept_quiz_score,
            "coding_score": concept_coding_score, "status": concept_status, "reasons": concept_reasons,
        })
    covered = sum(concept["status"] == "mastered" for concept in concepts)
    reasons = []
    if len(quizzes) < minimum_quizzes:
        reasons.append(f"Need {minimum_quizzes} distinct fresh quiz checks; have {len(quizzes)}.")
    if quiz_score is None or quiz_score < 80:
        reasons.append("Fresh quiz average must be at least 80.")
    if coding_required and (coding_score is None or coding_score < 80):
        reasons.append("This lesson requires server-verified coding evidence averaging at least 80.")
    if covered < minimum_concepts or covered < len(expected_concepts):
        reasons.append("Assess every quiz concept at 80 or above, covering two concepts when available.")
    assessment_kinds = ("quiz", "coding") if coding_required else ("quiz",)
    stale = [item for item in latest.values() if item["kind"] in assessment_kinds and not _fresh(item, now)]
    if stale:
        reasons.append("Evidence expires after 14 days; stale checks need reassessment.")
    mastered = (
        len(quizzes) >= minimum_quizzes and quiz_score is not None and quiz_score >= 80
        and (not coding_required or (coding_score is not None and coding_score >= 80))
        and covered >= minimum_concepts and covered == len(expected_concepts) and score >= 80
    )
    if mastered:
        status = "mastered"
        reasons.insert(0, "Fresh distinct assessments satisfy quiz, concept coverage and lesson policy thresholds.")
    elif any(item["score"] < 80 for item in quizzes + (coding if coding_required else [])) or not latest:
        status = "weak"
    else:
        status = "review"
    missed = []
    for item in latest.values():
        if item["kind"] == "quiz" and item["score"] < 80:
            missed.append({
                **public_check(check_map[item["source_id"]]), "score": item["score"],
                "recorded_at": _timestamp(item.get("recorded_at")), "needs_reassessment": not _fresh(item, now),
            })
    quiz_by_id = {item["source_id"]: item for item in latest.values() if item["kind"] == "quiz"}
    next_check = next((check for check in checks if (
        check["block_id"] not in quiz_by_id or not _fresh(quiz_by_id[check["block_id"]], now)
        or quiz_by_id[check["block_id"]]["score"] < 80
    )), None)
    if next_check:
        next_activity = {
            "kind": "quiz", "source_id": next_check["block_id"], "concept_id": next_check["concept_id"],
            "reason": "Attempt an unseen, missed or stale check to provide fresh concept evidence.",
        }
    elif coding_required and (coding_score is None or coding_score < 80):
        next_activity = {"kind": "coding", "reason": "Complete server-verified coding practice at 80 or above."}
    elif mastered:
        next_activity = {"kind": "review", "reason": "Reassess before evidence reaches 14 days old."}
    else:
        next_activity = {"kind": "lesson", "reason": "More distinct checks are needed; repetitions do not increase coverage."}
    assessments = quizzes + (coding if coding_required else [])
    review_after = min((_timestamp(item["recorded_at"]) + REASSESS_AFTER for item in assessments), default=None)
    return {
        "topic_slug": topic["slug"], "score": round(score, 2), "status": status,
        "quiz_score": quiz_score, "coding_score": coding_score, "coding_required": coding_required,
        "minimum_quizzes": minimum_quizzes, "minimum_concepts": minimum_concepts,
        "concepts": concepts, "reasons": reasons, "missed_questions": missed, "next_activity": next_activity,
        "evidence_counts": {kind: sum(item["kind"] == kind for item in fresh) for kind in KINDS},
        "retained_evidence_count": len(latest), "review_after": review_after if mastered else None,
    }


async def record_evidence(user_id, topic_slug, kind, score, source_id, concept_id=None):
    """Trusted server callers only; atomically replace latest evidence per (kind, source)."""
    key = mastery_key(user_id, topic_slug)
    if kind not in KINDS:
        raise ValueError("Invalid evidence kind")
    if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 100:
        raise ValueError("Evidence score must be a finite number from 0 to 100")
    _identifier(source_id, "source ID")
    if concept_id is not None:
        _identifier(concept_id, "concept ID")
    topic = await load_topic(topic_slug)
    if topic is None:
        raise ValueError("Topic not found")
    summarize_mastery(topic)
    if kind == "quiz":
        check = next((check for check in topic_checks(topic) if check["block_id"] == source_id), None)
        if check is None or (concept_id is not None and concept_id != check["concept_id"]):
            raise ValueError("Quiz evidence must match a catalog check and concept")
        concept_id = check["concept_id"]
    pipeline = [{"$set": {
        "user_id": {"$literal": key["user_id"]}, "topic_slug": {"$literal": topic_slug},
        "schema_version": 1, "updated_at": "$$NOW",
        "evidence": {"$slice": [{"$concatArrays": [
            {"$filter": {"input": {"$ifNull": ["$evidence", []]}, "as": "item", "cond": {"$not": [{"$and": [
                {"$eq": ["$$item.kind", {"$literal": kind}]},
                {"$eq": ["$$item.source_id", {"$literal": source_id}]},
            ]}]}}},
            [{"kind": {"$literal": kind}, "score": score, "source_id": {"$literal": source_id},
              "concept_id": {"$literal": concept_id}, "recorded_at": "$$NOW"}],
        ]}, -MAX_EVIDENCE]},
    }}]
    collection = get_collection("user_mastery")
    try:
        document = await collection.find_one_and_update(key, pipeline, upsert=True, return_document=ReturnDocument.AFTER)
    except DuplicateKeyError:
        document = await collection.find_one_and_update(key, pipeline, upsert=False, return_document=ReturnDocument.AFTER)
    if document is None:
        raise RuntimeError("Mastery evidence could not be recorded")
    return summarize_mastery(topic, document)
