$ErrorActionPreference = "Stop"
$repoRoot = (Get-Location).Path
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Patch-UniqueLine($relativePath, $oldLine, $newLine) {
    $target = Join-Path $repoRoot $relativePath
    $content = [System.IO.File]::ReadAllText($target)
    $count = ([regex]::Matches($content, [regex]::Escape($oldLine))).Count
    if ($count -ne 1) {
        throw "Expected exactly 1 match of anchor in $relativePath, found $count. Aborting patch for safety."
    }
    $content = $content.Replace($oldLine, $newLine)
    [System.IO.File]::WriteAllText($target, $content, $utf8NoBom)
    Write-Host "Patched: $relativePath"
}

$ddOld = '@router.get("/{slug}/details", response_model=DomainDetailResponse)'
$ddNew = '@router.get("/with-details")' + "`r`n" + `
'async def list_domains_with_details():' + "`r`n" + `
'    """Return only domains that actually have a domain_details document,' + "`r`n" + `
'    so the Mock Interview domain-picker never links to a domain that' + "`r`n" + `
'    would 404."""' + "`r`n" + `
'    details_coll = get_collection("domain_details")' + "`r`n" + `
'    slugs = [doc["domain_slug"] async for doc in details_coll.find({}, {"domain_slug": 1})]' + "`r`n" + `
'    domains_coll = get_collection("domains")' + "`r`n" + `
'    cursor = domains_coll.find({"$in": {"slug": slugs}})' + "`r`n" + `
'    result = []' + "`r`n" + `
'    async for doc in cursor:' + "`r`n" + `
'        doc.pop("_id", None)' + "`r`n" + `
'        result.append(doc)' + "`r`n" + `
'    return result' + "`r`n" + `
'' + "`r`n" + `
'@router.get("/{slug}/details", response_model=DomainDetailResponse)'
Patch-UniqueLine "backend\routes\domain_details.py" $ddOld $ddNew

$mainOld = 'app.include_router(resume.router)'
$mainNew = 'app.include_router(resume.router)' + "`r`n`r`n" + `
'@app.get("/mock-interview")' + "`r`n" + `
'async def mock_interview_page():' + "`r`n" + `
'    return FileResponse("frontend/mock-interview.html")'
Patch-UniqueLine "backend\main.py" $mainOld $mainNew

$miJsOld = '    ["mi-mode-select", "mi-interview-body", "mi-feedback-body", "mi-summary-body", "mi-loading"].forEach((id) => {'
$miJsNew = '    ["mi-domain-select", "mi-mode-select", "mi-interview-body", "mi-feedback-body", "mi-summary-body", "mi-loading"].forEach((id) => {'
Patch-UniqueLine "frontend\js\mock-interview.js" $miJsOld $miJsNew

$dashNavOld = '            <a href="/aptitude" class="btn-secondary" style="text-decoration: none; border-color: var(--accent-secondary); color: var(--accent-secondary); margin-right: 8px;">Aptitude Test</a>'
$dashNavNew = $dashNavOld + "`r`n" + '            <a href="/mock-interview" class="btn-secondary" style="text-decoration: none; border-color: var(--accent-yellow); color: var(--accent-yellow); margin-right: 8px;">Mock Interview</a>'
Patch-UniqueLine "frontend\dashboard.html" $dashNavOld $dashNavNew

$roadmapNavOld = '            <a href="/playground" class="btn-secondary">Playground</a>'
$roadmapNavNew = $roadmapNavOld + "`r`n" + '            <a href="/mock-interview" class="btn-secondary" style="border-color: var(--accent-yellow); color: var(--accent-yellow);">Mock Interview</a>'
Patch-UniqueLine "frontend\roadmap.html" $roadmapNavOld $roadmapNavNew

Write-Host "`n=== Step 1 patches done ===" -ForegroundColor Green