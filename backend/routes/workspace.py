import asyncio
import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.errors import PyMongoError

from backend.auth import get_current_user
from backend.config import settings
from backend.database import get_collection
from backend.mastery import summarize_mastery
from backend.routes.content import builtin_curriculum


router = APIRouter(tags=["workspace"])
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WINDOW = 100


def lesson_card(topic):
    slug = topic.get("slug", "")
    if not isinstance(slug, str) or len(slug) > 128 or not SLUG.fullmatch(slug):
        return None
    return {"slug": slug, "title": str(topic.get("title") or slug)[:240],
            "domain_slug": str(topic.get("domain_slug") or "")[:128],
            "difficulty": str(topic.get("difficulty") or "beginner")[:24]}


async def recent(collection, owner, projection):
    cursor = get_collection(collection).find({"user_id": owner}, projection)
    return [document async for document in cursor.sort("updated_at", -1).limit(WINDOW + 1).max_time_ms(3000)]


@router.get("/workspace/overview")
async def overview(current_user: dict = Depends(get_current_user)):
    try:
        owner = ObjectId(current_user["id"])
    except (InvalidId, TypeError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Sign in again to load your workspace.") from None
    progress, mastery = await asyncio.gather(
        recent("user_progress", owner, {"topic_slug": 1, "status": 1, "updated_at": 1}),
        recent("user_mastery", owner, {"topic_slug": 1, "evidence": 1, "updated_at": 1}),
    )
    limited = len(progress) > WINDOW or len(mastery) > WINDOW
    progress, mastery = progress[:WINDOW], mastery[:WINDOW]
    slugs = list({document.get("topic_slug") for document in progress + mastery if isinstance(document.get("topic_slug"), str)})
    topics = {topic["slug"]: topic for topic in builtin_curriculum()["topics"]}
    if slugs:
        cursor = get_collection("topics").find({"slug": {"$in": slugs}}, {
            "slug": 1, "title": 1, "domain_slug": 1, "difficulty": 1,
            "subtopics": 1, "content_blocks": 1, "mastery_policy": 1,
        }).limit(WINDOW * 2).max_time_ms(3000)
        async for topic in cursor:
            topics[topic["slug"]] = topic
    continuing, reviews = [], []
    seen = set()
    mastered = 0
    unavailable = 0
    for document in mastery:
        topic = topics.get(document.get("topic_slug"))
        card = lesson_card(topic) if topic else None
        if not card:
            unavailable += 1
            continue
        try:
            summary = summarize_mastery(topic, document)
        except (ValueError, TypeError, AttributeError):
            unavailable += 1
            continue
        if summary["status"] == "mastered":
            mastered += 1
            seen.add(card["slug"])
        elif summary["retained_evidence_count"]:
            reviews.append({**card, "reason": summary["next_activity"]["reason"], "kind": summary["next_activity"]["kind"]})
            seen.add(card["slug"])
    for document in progress:
        if document.get("status") != "in_progress" or document.get("topic_slug") in seen:
            continue
        topic = topics.get(document.get("topic_slug"))
        card = lesson_card(topic) if topic else None
        if card:
            continuing.append({**card, "reason": "You started this lesson. Continue where your understanding left off.", "kind": "lesson"})
            seen.add(card["slug"])
        else:
            unavailable += 1
    completed = {document.get("topic_slug") for document in progress if document.get("status") == "completed"}
    first = next((lesson_card(topic) for topic in builtin_curriculum()["topics"] if topic["slug"] not in completed | seen and lesson_card(topic)), None)
    return {
        "continue": continuing[:3], "reviews": reviews[:4], "suggested": first,
        "counts": {"in_progress": len(continuing), "review": len(reviews), "mastered": mastered},
        "limited": limited, "unavailable_lessons": unavailable,
        "has_history": bool(progress or mastery),
        "window": WINDOW, "generated_at": datetime.now(timezone.utc),
        "capabilities": {"ai_configured": bool(settings.GROQ_API_KEY), "runner_configured": bool(settings.PISTON_EXECUTE_URL)},
    }


@router.get("/catalog/search")
async def search(q: str = Query(default="", max_length=80)):
    query = " ".join(q.split())
    if len(query) < 2:
        return {"results": [], "degraded": False}
    terms = query.casefold().split()
    builtin = builtin_curriculum()["topics"]
    matches = {topic["slug"]: topic for topic in builtin if all(term in f"{topic['title']} {topic['domain_slug']}".casefold() for term in terms)}
    degraded = False
    try:
        pattern = {"$and": [{"$or": [{"title": {"$regex": re.escape(term), "$options": "i"}}, {"domain_slug": {"$regex": re.escape(term), "$options": "i"}}]} for term in terms]}
        cursor = get_collection("topics").find(pattern, {"slug": 1, "title": 1, "domain_slug": 1, "difficulty": 1}).sort("title", 1).limit(20).max_time_ms(2000)
        async for topic in cursor:
            if lesson_card(topic):
                matches[topic["slug"]] = topic
    except PyMongoError:
        degraded = True
    results = [lesson_card(topic) for topic in matches.values()]
    results = sorted((card for card in results if card), key=lambda card: (not card["title"].casefold().startswith(query.casefold()), card["title"].casefold()))[:12]
    return {"results": results, "degraded": degraded}
