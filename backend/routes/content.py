from copy import deepcopy
from functools import lru_cache
from typing import List

from fastapi import APIRouter, HTTPException
from pymongo.errors import PyMongoError

from backend.curriculum import load_curriculum
from backend.database import get_collection
from backend.models import DomainResponse, TopicResponse

router = APIRouter(tags=["content"])


@lru_cache(maxsize=1)
def builtin_curriculum():
    return load_curriculum()


def serialize_doc(document):
    result = deepcopy(document)
    result["id"] = str(result.pop("_id", result.get("id", f"curriculum:{result.get('slug', '')}")))
    return result


def public_topic(document):
    topic = serialize_doc(document)
    sections = [topic] + (topic.get("subtopics") or [])
    for section in sections:
        for block in section.get("content_blocks") or []:
            if block.get("type") == "knowledge_check":
                block.pop("correct_index", None)
                block.pop("explanation", None)
    return topic


@router.get("/curriculum")
async def curriculum_catalog():
    data = builtin_curriculum()
    return {
        "domains": [serialize_doc(document) for document in data["domains"]],
        "topics": [{key: topic[key] for key in ("slug", "title", "domain_slug", "difficulty", "order", "objectives", "prerequisites")} for topic in data["topics"]],
    }


@router.get("/domains", response_model=List[DomainResponse])
async def list_domains():
    documents = [serialize_doc(document) async for document in get_collection("domains").find().limit(100).max_time_ms(5000)]
    existing = {document["slug"] for document in documents}
    return documents + [serialize_doc(document) for document in builtin_curriculum()["domains"] if document["slug"] not in existing]


@router.get("/domains/{slug}/topics", response_model=List[TopicResponse])
async def list_domain_topics(slug: str):
    builtin_domain = next((domain for domain in builtin_curriculum()["domains"] if domain["slug"] == slug), None)
    try:
        domain = await get_collection("domains").find_one({"slug": slug})
        if not domain and not builtin_domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        documents = [public_topic(document) async for document in get_collection("topics").find({"domain_slug": slug}).limit(500).max_time_ms(5000)]
    except PyMongoError:
        if not builtin_domain:
            raise
        documents = []
    existing = {document["slug"] for document in documents}
    documents += [public_topic(document) for document in builtin_curriculum()["topics"] if document["domain_slug"] == slug and document["slug"] not in existing]
    return sorted(documents, key=lambda topic: (topic.get("order", 999), topic["title"]))


@router.get("/topics/{slug}", response_model=TopicResponse)
async def get_topic(slug: str):
    builtin = next((topic for topic in builtin_curriculum()["topics"] if topic["slug"] == slug), None)
    try:
        topic = await get_collection("topics").find_one({"slug": slug})
    except PyMongoError:
        if not builtin:
            raise
        topic = None
    topic = topic or builtin
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return public_topic(topic)
