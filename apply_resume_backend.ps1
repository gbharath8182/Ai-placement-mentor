$resumeContent = @'
import json
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.config import settings

router = APIRouter(prefix="/resume", tags=["resume"])


class ProjectInput(BaseModel):
    title: str
    description: str


class ResumeGenerateRequest(BaseModel):
    full_name: str
    target_role: str
    experience_level: str = "fresher"  # fresher, intermediate, experienced
    skills: List[str] = []
    projects: List[ProjectInput] = []
    education: str = ""
    achievements: List[str] = []
    tone: str = "concise"  # concise, detailed


async def call_groq_text(messages: list, model: str) -> str:
    if not settings.GROQ_API_KEY:
        return (
            "# [Demonstration Mode]\n\n"
            "GROQ_API_KEY is not configured in your .env file, so this is placeholder text. "
            "Add GROQ_API_KEY to enable real resume generation."
        )

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {"model": model, "messages": messages, "temperature": 0.5, "stream": False}

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers, json=body, timeout=60.0
            )
            if r.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Groq API error ({r.status_code}): {r.text}"
                )
            res = r.json()
            return res["choices"][0]["message"]["content"]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Exception connecting to Groq: {str(e)}"
            )


@router.post("/generate")
async def generate_resume(req: ResumeGenerateRequest, current_user: dict = Depends(get_current_user)):
    if not req.full_name.strip() or not req.target_role.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="full_name and target_role are required"
        )

    projects_str = "\n".join(
        f"- {p.title}: {p.description}" for p in req.projects
    ) if req.projects else "(none provided)"
    skills_str = ", ".join(req.skills) if req.skills else "(none provided)"
    achievements_str = "\n".join(f"- {a}" for a in req.achievements) if req.achievements else "(none provided)"

    tone_instruction = (
        "Keep it concise and punchy - one page worth of content, tight bullet points."
        if req.tone == "concise" else
        "Provide fuller detail on each point - this can run slightly longer than one page."
    )

    system_prompt = (
        "You are an expert technical resume writer helping students and early-career "
        "candidates create genuinely strong, honest, ATS-friendly resumes for real job "
        "applications. Do not invent facts, companies, numbers, or experience the candidate "
        "did not provide - only elaborate on and better phrase what they gave you.\n\n"
        f"Candidate name: {req.full_name}\n"
        f"Target role/domain: {req.target_role}\n"
        f"Experience level: {req.experience_level}\n"
        f"Skills: {skills_str}\n"
        f"Projects:\n{projects_str}\n"
        f"Education: {req.education or '(none provided)'}\n"
        f"Achievements/certifications:\n{achievements_str}\n\n"
        f"{tone_instruction}\n\n"
        "Output a complete resume in clean Markdown with these sections in order: "
        "# {Full Name}, a one-line contact/title placeholder, ## Summary (2-3 sentences), "
        "## Skills (grouped, as a bullet or comma list), ## Projects (bullet points per "
        "project, action-verb-led, quantify impact only if the candidate's description "
        "supports it), ## Education, and ## Achievements & Certifications (omit this "
        "section entirely if none were provided). Do not add any explanation before or "
        "after the resume - output ONLY the Markdown resume itself."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Generate my resume."}
    ]

    resume_markdown = await call_groq_text(messages, settings.GROQ_FALLBACK_MODEL)
    return {"resume_markdown": resume_markdown, "model_used": settings.GROQ_FALLBACK_MODEL}
'@

$mainPatchScript = @'
path = "backend/main.py"
with open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

if "resume" in content and "from backend.routes import" in content and "resume" in content.split("from backend.routes import")[1].split("\n")[0]:
    print("SKIPPED: main.py import already patched")
else:
    old_import = "from backend.routes import auth, content, ai, practice, progress, domain_details, activity, analytics, mock_interview"
    assert old_import in content, "PATCH FAILED: import line not found - check current main.py content"
    new_import = old_import + ", resume"
    content = content.replace(old_import, new_import)

    old_router = "app.include_router(mock_interview.router)"
    assert content.count(old_router) == 1, "PATCH FAILED: mock_interview router line not found or not unique"
    new_router = old_router + "\r\napp.include_router(resume.router)"
    content = content.replace(old_router, new_router)

    old_route_anchor = '@app.get("/analytics")\r\nasync def read_analytics_page():\r\n    return FileResponse("frontend/analytics.html")'
    assert old_route_anchor in content, "PATCH FAILED: analytics page route not found - check current main.py content"
    new_route = old_route_anchor + '\r\n\r\n@app.get("/resume")\r\nasync def read_resume_page():\r\n    return FileResponse("frontend/resume.html")'
    content = content.replace(old_route_anchor, new_route)

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    print("main.py patched successfully")
'@

$repoRoot = (Get-Location).Path

$resumeTargetPath = Join-Path $repoRoot "backend\routes\resume.py"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($resumeTargetPath, $resumeContent, $utf8NoBom)
Write-Host "resume.py written." -ForegroundColor Cyan

$mainPatchPath = Join-Path $repoRoot "patch_main_resume.py"
[System.IO.File]::WriteAllText($mainPatchPath, $mainPatchScript, $utf8NoBom)
python patch_main_resume.py

Write-Host "`nVerifying resume.py syntax..." -ForegroundColor Cyan
python -c "import ast; ast.parse(open('backend/routes/resume.py', encoding='utf-8').read()); print('resume.py SYNTAX OK')"

Write-Host "Verifying main.py syntax..." -ForegroundColor Cyan
python -c "import ast; ast.parse(open('backend/main.py', encoding='utf-8').read()); print('main.py SYNTAX OK')"