from fastapi import APIRouter, Depends, HTTPException, status
from backend.database import get_collection
from backend.models import ProgressUpdate
from backend.auth import get_current_user
from bson import ObjectId
from datetime import datetime, timezone
from typing import List

router = APIRouter(prefix="/progress", tags=["progress"])

def serialize_progress(doc):
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    doc["user_id"] = str(doc["user_id"])
    del doc["_id"]
    return doc

@router.get("/{user_id}")
async def get_user_progress(user_id: str, current_user: dict = Depends(get_current_user)):
    # Check if the user is authorized to view this progress
    if current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this user's progress"
        )
        
    progress_coll = get_collection("user_progress")
    cursor = progress_coll.find({"user_id": ObjectId(user_id)})
    
    progress_list = []
    async for doc in cursor:
        progress_list.append(serialize_progress(doc))
    return progress_list

@router.post("/update")
async def update_progress(req: ProgressUpdate, current_user: dict = Depends(get_current_user)):
    progress_coll = get_collection("user_progress")
    
    update_data = {
        "status": req.status,
        "updated_at": datetime.now(timezone.utc)
    }
    if req.ai_notes is not None:
        update_data["ai_notes"] = req.ai_notes
        
    await progress_coll.update_one(
        {
            "user_id": ObjectId(current_user["id"]),
            "topic_slug": req.topic_slug
        },
        {
            "$set": update_data
        },
        upsert=True
    )
    
    return {"message": "Progress updated successfully", "topic_slug": req.topic_slug, "status": req.status}
