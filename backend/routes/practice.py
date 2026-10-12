import asyncio
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Depends, Path, Query
from backend.database import get_collection
from backend.models import PracticeProblemResponse, CodeSubmitRequest
from backend.auth import get_current_user
from backend.config import settings
from typing import List
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
from bson.errors import InvalidId
import httpx

router = APIRouter(prefix="/practice", tags=["practice"])

MAX_TEST_CASES = 20
MAX_TEST_BYTES = 16384
MAX_SANDBOX_RESPONSE_BYTES = 65536
SUBMISSION_TIMEOUT_SECONDS = 30


class RunTestCase(BaseModel):
    input: str = Field(max_length=MAX_TEST_BYTES)
    expected_output: str = Field(max_length=MAX_TEST_BYTES)

    @field_validator("input", "expected_output")
    @classmethod
    def bound_test_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_TEST_BYTES:
            raise ValueError("Test input/output cannot exceed 16 KiB")
        return value


class CodeRunRequest(CodeSubmitRequest):
    test_cases: List[RunTestCase] = Field(min_length=1, max_length=MAX_TEST_CASES)

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
    serialized = dict(doc)
    serialized["id"] = str(serialized.pop("_id", serialized.get("id")))
    serialized.pop("reference_solution", None)
    return serialized


def parse_problem_id(problem_id: str) -> ObjectId:
    try:
        return ObjectId(problem_id)
    except (InvalidId, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid problem ID format")


def builtin_problems() -> list:
    try:
        from backend.curriculum import load_practice
    except ImportError:
        raise HTTPException(status_code=503, detail="Built-in practice curriculum unavailable") from None
    return load_practice()


async def get_problem(problem_id: str):
    object_id = parse_problem_id(problem_id)
    problem = await get_collection("practice_problems").find_one({"_id": object_id})
    if problem:
        return problem
    for builtin in builtin_problems():
        if str(builtin.get("_id", builtin.get("id"))) == str(object_id):
            problem = dict(builtin)
            problem["_id"] = object_id
            return problem
    return None


def sandbox_url() -> str:
    endpoint = getattr(settings, "PISTON_EXECUTE_URL", "") or os.getenv("PISTON_EXECUTE_URL", "")
    if not endpoint:
        raise HTTPException(status_code=503, detail="Remote execution is not configured")
    try:
        parsed = urlsplit(endpoint)
        valid = (parsed.scheme == "https" and parsed.hostname and not parsed.username
                 and not parsed.password and not parsed.query and not parsed.fragment)
        parsed.port
    except ValueError:
        valid = False
    if not valid:
        raise HTTPException(status_code=503, detail="Remote execution requires a trusted HTTPS sandbox")
    return endpoint


async def execute_test_case(client: httpx.AsyncClient, endpoint: str, submission: CodeSubmitRequest, test_case: dict):
    runtime = PISTON_LANG_MAP[submission.language]
    code = submission.code
    if submission.language == "javascript":
        code = ('const inputLines=require("fs").readFileSync(0,"utf8").split(/\\r?\\n/);'
                'let inputCursor=0;const prompt=()=>inputLines[inputCursor++]||"";\n' + code)
    payload = {
        "language": runtime["name"], "version": runtime["version"],
        "files": [{"name": runtime["filename"], "content": code}],
        "stdin": test_case["input"], "args": [],
        "compile_timeout": 10000, "run_timeout": 3000,
        "compile_cpu_time": 10000, "run_cpu_time": 3000,
        "compile_memory_limit": 256 * 1024 * 1024, "run_memory_limit": 128 * 1024 * 1024,
    }
    async with client.stream("POST", endpoint, json=payload) as remote_response:
        remote_response.raise_for_status()
        content = bytearray()
        async for chunk in remote_response.aiter_bytes(chunk_size=8192):
            if len(content) + len(chunk) > MAX_SANDBOX_RESPONSE_BYTES:
                raise HTTPException(status_code=502, detail="Sandbox response exceeds output limit")
            content.extend(chunk)
    try:
        result = json.loads(content)
        if not isinstance(result, dict):
            raise ValueError()
        run = result.get("run")
        compiled = result.get("compile")
        if compiled is not None and not isinstance(compiled, dict):
            raise ValueError()
        compile_failed = compiled is not None and (compiled.get("code") != 0 or compiled.get("signal") is not None)
        stage = compiled if compile_failed else run
        if not isinstance(stage, dict):
            raise ValueError()
        stdout, stderr = stage.get("stdout"), stage.get("stderr")
        if (not isinstance(stdout, str) or not isinstance(stderr, str)
                or "code" not in stage
                or type(stage.get("code")) not in (int, type(None))
                or (stage.get("code") is None and not stage.get("signal"))
                or (stage.get("signal") is not None and not isinstance(stage["signal"], str))):
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(status_code=502, detail="Invalid sandbox response")
    actual = stdout.replace("\r\n", "\n").strip()
    expected = test_case["expected_output"].replace("\r\n", "\n").strip()
    return {
        "input": test_case["input"], "expected": test_case["expected_output"],
        "actual": stdout, "stderr": stderr,
        "passed": not compile_failed and stage.get("code") == 0 and stage.get("signal") is None and not stderr and actual == expected,
    }


async def execute_cases(endpoint: str, submission: CodeSubmitRequest, test_cases: list):
    api_key = getattr(settings, "PISTON_API_KEY", "")
    if not isinstance(api_key, str) or len(api_key) > 4096 or "\r" in api_key or "\n" in api_key:
        raise HTTPException(status_code=503, detail="Invalid sandbox authentication configuration")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    results = []
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(15, connect=3, pool=3),
        follow_redirects=False, trust_env=False, headers=headers,
        limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
    ) as client:
        for index, test_case in enumerate(test_cases):
            result = await execute_test_case(client, endpoint, submission, test_case)
            result["test_case_index"] = index
            results.append(result)
    return results


@router.post("/run")
async def run_code(submission: CodeRunRequest, current_user: dict = Depends(get_current_user)):
    endpoint = sandbox_url()
    test_cases = [test_case.model_dump() for test_case in submission.test_cases]
    try:
        results = await asyncio.wait_for(
            execute_cases(endpoint, submission, test_cases), timeout=SUBMISSION_TIMEOUT_SECONDS,
        )
    except (asyncio.TimeoutError, httpx.TimeoutException):
        raise HTTPException(status_code=504, detail="Sandbox execution timed out")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Sandbox execution unavailable")
    return {"results": results, "overall_passed": all(result["passed"] for result in results)}


@router.post("/{problem_id}/submit")
async def submit_code(problem_id: str, submission: CodeSubmitRequest, current_user: dict = Depends(get_current_user)):
    object_id = parse_problem_id(problem_id)
    endpoint = sandbox_url()

    async def execute_submission():
        try:
            from backend.mastery import record_evidence
        except ImportError:
            raise HTTPException(status_code=503, detail="Coding mastery integration unavailable") from None

        problem = await get_problem(str(object_id))
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")
        topic_slug = problem.get("topic_slug")
        if not isinstance(topic_slug, str) or not 1 <= len(topic_slug) <= 128:
            raise HTTPException(status_code=422, detail="Invalid problem topic")
        test_cases = problem.get("test_cases")
        if not isinstance(test_cases, list) or not 1 <= len(test_cases) <= MAX_TEST_CASES:
            raise HTTPException(status_code=422, detail="Problem test cases exceed execution bounds")
        for test_case in test_cases:
            if not isinstance(test_case, dict):
                raise HTTPException(status_code=422, detail="Invalid problem test case")
            for key in ("input", "expected_output"):
                value = test_case.get(key)
                if not isinstance(value, str) or len(value.encode("utf-8")) > MAX_TEST_BYTES:
                    raise HTTPException(status_code=422, detail="Problem test case exceeds input/output bounds")
        results = await execute_cases(endpoint, submission, test_cases)
        passed_count = sum(result["passed"] for result in results)
        score = 100.0 * passed_count / len(results)
        await record_evidence(current_user["id"], topic_slug, "coding", score, source_id=str(object_id))
        overall_passed = passed_count == len(results)
        if overall_passed:
            await get_collection("user_progress").update_one(
                {"user_id": ObjectId(current_user["id"]), "topic_slug": topic_slug},
                {"$set": {"status": "completed", "updated_at": datetime.now(timezone.utc)}},
                upsert=True,
            )
        return {"results": results, "overall_passed": overall_passed}

    try:
        return await asyncio.wait_for(execute_submission(), timeout=SUBMISSION_TIMEOUT_SECONDS)
    except (asyncio.TimeoutError, httpx.TimeoutException):
        raise HTTPException(status_code=504, detail="Sandbox execution timed out")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Sandbox execution unavailable")

@router.get("/{topic_slug}", response_model=List[PracticeProblemResponse])
async def get_practice_problems(
    topic_slug: str = Path(min_length=1, max_length=128),
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
):
    problems_coll = get_collection("practice_problems")
    cursor = problems_coll.find({"topic_slug": topic_slug}).skip(offset).limit(limit).max_time_ms(5000)
    problems = []
    async for doc in cursor:
        problems.append(serialize_problem(doc))
    if not problems:
        if offset and await problems_coll.find_one({"topic_slug": topic_slug}):
            return problems
        matches = [serialize_problem(problem) for problem in builtin_problems() if problem.get("topic_slug") == topic_slug]
        problems = matches[offset:offset + limit]
    return problems

@router.post("/{problem_id}/completed")
async def mark_problem_completed(
    problem_id: str, 
    current_user: dict = Depends(get_current_user)
):
    raise HTTPException(status_code=409, detail="Use POST /practice/{problem_id}/submit for server-verified completion")
