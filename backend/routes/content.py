from fastapi import APIRouter, HTTPException, status
from backend.database import get_collection
from backend.models import DomainResponse, TopicResponse
from typing import List
from bson import ObjectId

router = APIRouter(prefix="", tags=["content"])

def serialize_doc(doc):
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

@router.get("/domains", response_model=List[DomainResponse])
async def list_domains():
    domains_coll = get_collection("domains")
    cursor = domains_coll.find()
    domains = []
    async for doc in cursor:
        domains.append(serialize_doc(doc))
    return domains

@router.get("/domains/{slug}/topics", response_model=List[TopicResponse])
async def list_domain_topics(slug: str):
    # Find domain to ensure it exists
    domains_coll = get_collection("domains")
    domain = await domains_coll.find_one({"slug": slug})
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{slug}' not found"
        )
        
    topics_coll = get_collection("topics")
    cursor = topics_coll.find({"domain_slug": slug})
    topics = []
    async for doc in cursor:
        topics.append(serialize_doc(doc))
    return topics

@router.get("/topics/{slug}", response_model=TopicResponse)
async def get_topic(slug: str):
    topics_coll = get_collection("topics")
    topic = await topics_coll.find_one({"slug": slug})
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic '{slug}' not found"
        )
    return serialize_doc(topic)
