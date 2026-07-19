$ErrorActionPreference = "Stop"
$repoRoot = (Get-Location).Path
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$target = Join-Path $repoRoot "backend\routes\domain_details.py"
$content = [System.IO.File]::ReadAllText($target)

$old = 'cursor = domains_coll.find({"$in": {"slug": slugs}})'
$new = 'cursor = domains_coll.find({"slug": {"$in": slugs}})'

$count = ([regex]::Matches($content, [regex]::Escape($old))).Count
if ($count -ne 1) {
    throw "Expected exactly 1 match, found $count. Aborting for safety."
}
$content = $content.Replace($old, $new)
[System.IO.File]::WriteAllText($target, $content, $utf8NoBom)
Write-Host "Fixed query in domain_details.py"