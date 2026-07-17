from fastapi import APIRouter, HTTPException, Depends, status
from backend.database import get_collection
from backend.models import PracticeProblemResponse, CodeSubmitRequest
from backend.auth import get_current_user
from typing import List
from bson import ObjectId
import httpx

router = APIRouter(prefix="/practice", tags=["practice"])

PISTON_LANG_MAP = {
    "python": {"name": "python", "version": "3.10.0", "filename": "main.py"},
    "javascript": {"name": "javascript", "version": "18.15.0", "filename": "main.js"},
    "cpp": {"name": "c++", "version": "10.2.0", "filename": "main.cpp"},
    "c": {"name": "c", "version": "10.2.0", "filename": "main.c"},
    "java": {"name": "java", "version": "15.0.2", "filename": "Main.java"}
}

def serialize_problem(doc):
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

@router.get("/{topic_slug}", response_model=List[PracticeProblemResponse])
async def get_practice_problems(topic_slug: str, current_user: dict = Depends(get_current_user)):
    problems_coll = get_collection("practice_problems")
    cursor = problems_coll.find({"topic_slug": topic_slug})
    problems = []
    async for doc in cursor:
        problems.append(serialize_problem(doc))
    return problems

@router.post("/{problem_id}/completed")
async def mark_problem_completed(
    problem_id: str, 
    current_user: dict = Depends(get_current_user)
):
    problems_coll = get_collection("practice_problems")
    
    try:
        problem = await problems_coll.find_one({"_id": ObjectId(problem_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid problem ID format")
        
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
        
    progress_coll = get_collection("user_progress")
    from datetime import datetime
    await progress_coll.update_one(
        {
            "user_id": ObjectId(current_user["id"]),
            "topic_slug": problem["topic_slug"]
        },
        {
            "$set": {
                "status": "completed",
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    return {
        "success": True
    }
