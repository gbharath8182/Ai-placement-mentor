$ErrorActionPreference = "Stop"
$repoRoot = (Get-Location).Path
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$target = Join-Path $repoRoot "backend\routes\mock_interview.py"
$content = [System.IO.File]::ReadAllText($target)

$old = '@router.post("/explain-more")'
$new = @'
class EndInterviewRequest(BaseModel):
    session_id: str


@router.post("/end")
async def end_mock_interview(req: EndInterviewRequest, current_user: dict = Depends(get_current_user)):
    """Lets a candidate stop early and still get scored on whatever
    questions they already answered, instead of requiring all
    num_questions to be completed."""
    session = interview_sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found or has expired")
    if session["user_id"] != str(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")

    scores = [r["score"] for r in session["results"]]
    average_score = round(sum(scores) / len(scores), 1) if scores else 0
    return {
        "summary": {
            "average_score": average_score,
            "questions_answered": len(session["results"]),
            "mode": session["mode"],
            "per_question": session["results"]
        }
    }


@router.post("/explain-more")
'@

$count = ([regex]::Matches($content, [regex]::Escape($old))).Count
if ($count -ne 1) { throw "Expected 1 match, found $count. Aborting." }
$content = $content.Replace($old, $new)
[System.IO.File]::WriteAllText($target, $content, $utf8NoBom)
Write-Host "Patched: backend\routes\mock_interview.py (added /end endpoint)"