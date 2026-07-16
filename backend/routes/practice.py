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

@router.post("/{problem_id}/run")
async def run_problem_code(
    problem_id: str, 
    req: CodeSubmitRequest, 
    current_user: dict = Depends(get_current_user)
):
    problems_coll = get_collection("practice_problems")
    
    try:
        problem = await problems_coll.find_one({"_id": ObjectId(problem_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid problem ID format")
        
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
        
    lang = req.language.lower()
    if lang not in PISTON_LANG_MAP:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported language '{req.language}'. Supported: Python, JavaScript, C++, C, Java"
        )
        
    piston_config = PISTON_LANG_MAP[lang]
    test_cases = problem.get("test_cases", [])
    
    if not test_cases:
        # If no test cases are specified, just run once with empty input
        test_cases = [{"input": "", "expected_output": ""}]
        
    results = []
    overall_passed = True
    
    async with httpx.AsyncClient() as client:
        for idx, tc in enumerate(test_cases):
            payload = {
                "language": piston_config["name"],
                "version": piston_config["version"],
                "files": [{
                    "name": piston_config["filename"],
                    "content": req.code
                }],
                "stdin": tc["input"],
                "compile_timeout": 10000,
                "run_timeout": 10000
            }
            
            try:
                r = await client.post(
                    "https://emkc.org/api/v2/piston/execute", 
                    json=payload, 
                    timeout=15.0
                )
            except Exception as e:
                raise HTTPException(
                    status_code=502, 
                    detail=f"Error connecting to Piston code execution API: {str(e)}"
                )
                
            if r.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Code execution API returned status {r.status_code}: {r.text}"
                )
                
            execution_res = r.json()
            run_data = execution_res.get("run", {})
            stdout = run_data.get("stdout", "")
            stderr = run_data.get("stderr", "")
            exit_code = run_data.get("code", 0)
            
            # Perform verification
            expected = tc.get("expected_output", "")
            passed = False
            
            if exit_code == 0 and not stderr:
                # Clean and compare stdout with expected output
                cleaned_stdout = stdout.strip().replace("\r\n", "\n")
                cleaned_expected = expected.strip().replace("\r\n", "\n")
                passed = (cleaned_stdout == cleaned_expected)
            else:
                passed = False
                overall_passed = False
                
            results.append({
                "test_case_index": idx,
                "input": tc["input"],
                "expected": expected,
                "actual": stdout.strip(),
                "stderr": stderr,
                "passed": passed
            })
            
            if not passed:
                overall_passed = False
                
    # Update progress if all test cases passed
    if overall_passed:
        progress_coll = get_collection("user_progress")
        await progress_coll.update_one(
            {
                "user_id": ObjectId(current_user["id"]),
                "topic_slug": problem["topic_slug"]
            },
            {
                "$set": {
                    "status": "completed",
                    "updated_at": None  # We'll set this to the current datetime
                }
            },
            upsert=True
        )
        
    return {
        "success": overall_passed,
        "results": results
    }
