from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, ConfigDict, Field

from backend.auth import get_current_user
from backend.database import get_collection
from backend.mastery import load_topic, mastery_key, record_evidence, serialize_checks, summarize_mastery, topic_checks


router = APIRouter(prefix="/learning", tags=["learning"])


class CheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block_id: str = Field(min_length=1, max_length=128, pattern=r"\S", strict=True)
    selected_index: int = Field(ge=0, le=19, strict=True)


async def _topic(topic_slug):
    try:
        topic = await load_topic(topic_slug)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Lesson checks are unavailable") from None
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    try:
        checks = topic_checks(topic)
        summarize_mastery(topic)
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=503, detail="Lesson checks are unavailable") from None
    return topic, checks


@router.get("/{topic_slug}/checks")
async def get_checks(
    topic_slug: str = Path(min_length=1, max_length=128),
    current_user: dict = Depends(get_current_user),
):
    topic, checks = await _topic(topic_slug)
    return {"topic_slug": topic_slug, "checks": serialize_checks(topic)}


@router.post("/{topic_slug}/check")
async def check_answer(
    request: CheckRequest,
    topic_slug: str = Path(min_length=1, max_length=128),
    current_user: dict = Depends(get_current_user),
):
    topic, checks = await _topic(topic_slug)
    check = next((check for check in checks if check["block_id"] == request.block_id), None)
    if check is None:
        raise HTTPException(status_code=404, detail="Check not found")
    if request.selected_index >= len(check["options"]):
        raise HTTPException(status_code=422, detail="Selected option is out of range")
    correct = request.selected_index == check["correct_index"]
    mastery = await record_evidence(
        current_user["id"], topic_slug, "quiz", 100 if correct else 0,
        source_id=check["block_id"], concept_id=check["concept_id"],
    )
    return {"correct": correct, "explanation": check["explanation"], "mastery": mastery}


@router.get("/{topic_slug}/mastery")
async def get_mastery(
    topic_slug: str = Path(min_length=1, max_length=128),
    current_user: dict = Depends(get_current_user),
):
    topic, checks = await _topic(topic_slug)
    document = await get_collection("user_mastery").find_one(mastery_key(current_user["id"], topic_slug))
    return summarize_mastery(topic, document)
