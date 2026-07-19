from fastapi import APIRouter, HTTPException, status
from backend.database import get_collection
from backend.models import DomainDetailResponse

router = APIRouter(prefix="/domains", tags=["domain-details"])

@router.get("/with-details")
async def list_domains_with_details():
    """Return every learning domain for the Mock Interview picker.

    A detailed roadmap is useful but must not be a gate for interview
    practice: newly-added domains can still receive AI-generated questions.
    """
    details_coll = get_collection("domain_details")
    slugs = [doc["domain_slug"] async for doc in details_coll.find({}, {"domain_slug": 1})]
    domains_coll = get_collection("domains")
    cursor = domains_coll.find()
    result = []
    async for doc in cursor:
        doc.pop("_id", None)
        doc["has_detailed_content"] = doc.get("slug") in slugs
        result.append(doc)
    return result

@router.get("/{slug}/details", response_model=DomainDetailResponse)
async def get_domain_details(slug: str):
    coll = get_collection("domain_details")
    doc = await coll.find_one({"domain_slug": slug})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detailed content for domain '{slug}' not found"
        )
    doc.pop("_id", None)
    return doc
