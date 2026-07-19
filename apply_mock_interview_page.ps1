$ErrorActionPreference = "Stop"
$repoRoot = (Get-Location).Path
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-FileNoBom($relativePath, $content) {
    $target = Join-Path $repoRoot $relativePath
    [System.IO.File]::WriteAllText($target, $content, $utf8NoBom)
    Write-Host "Wrote: $relativePath"
}

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

# ---- 1) domain_details.py: add GET /domains/with-details ----
$ddOld = '@router.get("/{slug}/details", response_model=DomainDetailResponse)'
$ddNew = @'
@router.get("/with-details")
async def list_domains_with_details():
    """Return only domains that actually have a domain_details document,
    so the Mock Interview domain-picker never links to a domain that
    would 404."""
    details_coll = get_collection("domain_details")
    slugs = [doc["domain_slug"] async for doc in details_coll.find({}, {"domain_slug": 1})]
    domains_coll = get_collection("domains")
    cursor = domains_coll.find({"slug": {"$in": slugs}})
    result = []
    async for doc in cursor:
        doc.pop("_id", None)
        result.append(doc)
    return result

@router.get("/{slug}/details", response_model=DomainDetailResponse)
'@
Patch-UniqueLine "backend\routes\domain_details.py" $ddOld $ddNew

# ---- 2) main.py: add /mock-interview page route ----
$mainOld = 'app.include_router(resume.router)'
$mainNew = @'
app.include_router(resume.router)

@app.get("/mock-interview")
async def mock_interview_page():
    return FileResponse("frontend/mock-interview.html")
'@
Patch-UniqueLine "backend\main.py" $mainOld $mainNew

# ---- 3) mock-interview.js: teach miShowPanel about the new domain-select panel ----
$miJsOld = '    ["mi-mode-select", "mi-interview-body", "mi-feedback-body", "mi-summary-body", "mi-loading"].forEach((id) => {'
$miJsNew = '    ["mi-domain-select", "mi-mode-select", "mi-interview-body", "mi-feedback-body", "mi-summary-body", "mi-loading"].forEach((id) => {'
Patch-UniqueLine "frontend\js\mock-interview.js" $miJsOld $miJsNew

# ---- 4) dashboard.html: add nav link ----
$dashNavOld = '            <a href="/aptitude" class="btn-secondary" style="text-decoration: none; border-color: var(--accent-secondary); color: var(--accent-secondary); margin-right: 8px;">Aptitude Test</a>'
$dashNavNew = @'
            <a href="/aptitude" class="btn-secondary" style="text-decoration: none; border-color: var(--accent-secondary); color: var(--accent-secondary); margin-right: 8px;">Aptitude Test</a>
            <a href="/mock-interview" class="btn-secondary" style="text-decoration: none; border-color: var(--accent-yellow); color: var(--accent-yellow); margin-right: 8px;">Mock Interview</a>
'@
Patch-UniqueLine "frontend\dashboard.html" $dashNavOld $dashNavNew

# ---- 5) roadmap.html: add nav link ----
$roadmapNavOld = '            <a href="/playground" class="btn-secondary">Playground</a>'
$roadmapNavNew = @'
            <a href="/playground" class="btn-secondary">Playground</a>
            <a href="/mock-interview" class="btn-secondary" style="border-color: var(--accent-yellow); color: var(--accent-yellow);">Mock Interview</a>
'@
Patch-UniqueLine "frontend\roadmap.html" $roadmapNavOld $roadmapNavNew

# ---- 6) New file: frontend/mock-interview.html ----
$mockInterviewHtml = @'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mock Interview - EduAI Platform</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav class="dashboard-nav">
        <a href="/dashboard" class="nav-brand"><span>EduAI Platform</span></a>
        <div class="nav-user">
            <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme"></button>
            <a href="/roadmap" class="btn-secondary">Roadmaps</a>
            <a href="/profile" class="btn-secondary">Profile</a>
            <a href="/analytics" class="btn-secondary">Analytics</a>
            <a href="/playground" class="btn-secondary">Playground</a>
            <a href="/mock-interview" class="btn-secondary nav-link-active" style="border-color: var(--accent-yellow); color: var(--accent-yellow);">Mock Interview</a>
            <a href="/dashboard" class="btn-secondary">Dashboard</a>
            <div class="user-badge"><span id="user-name">Learner</span></div>
        </div>
    </nav>

    <main class="mi-page-container">

        <div id="mi-loading" class="mi-page-panel glass-panel hidden">
            <p>Loading...</p>
        </div>

        <div id="mi-domain-select" class="mi-page-panel glass-panel">
            <h1>Mock Interview</h1>
            <p>Pick a domain to start a practice interview.</p>
            <div id="mi-domain-grid" class="mi-domain-grid"></div>
            <p id="mi-domain-empty" class="hidden" style="color: var(--text-muted);">
                No domains with interview content yet. Check back soon.
            </p>
        </div>

        <div id="mi-mode-select" class="mi-page-panel glass-panel hidden">
            <button class="mi-back-btn" id="mi-back-to-domains-1">&larr; Change domain</button>
            <h2>Start Mock Interview</h2>
            <p>Choose a mode to begin.</p>
            <div class="mi-mode-grid">
                <button class="mi-mode-btn" data-mode="coding">Coding<span class="mi-mode-desc">AI-generated coding questions for this domain</span></button>
                <button class="mi-mode-btn" data-mode="hr">HR / Behavioral<span class="mi-mode-desc">Soft skills, teamwork, innovation</span></button>
                <button class="mi-mode-btn" data-mode="technical">Technical Panel<span class="mi-mode-desc">In-depth engineering interview</span></button>
                <button class="mi-mode-btn" data-mode="mixed">Mixed<span class="mi-mode-desc">A bit of everything</span></button>
            </div>
        </div>

        <div id="mi-interview-body" class="mi-page-panel glass-panel hidden">
            <p id="mi-progress-text"></p>
            <span id="mi-category-badge"></span>
            <h3 id="mi-question-text"></h3>
            <textarea id="mi-answer-input" rows="8" placeholder="Type your answer..."></textarea>
            <button id="mi-submit-btn" class="btn-primary">Submit Answer</button>
        </div>

        <div id="mi-feedback-body" class="mi-page-panel glass-panel hidden">
            <h3>Score: <span id="mi-score-value"></span>/10</h3>
            <h4>Strengths</h4>
            <ul id="mi-strengths-list"></ul>
            <h4>Weaknesses</h4>
            <ul id="mi-weaknesses-list"></ul>
            <p id="mi-hint-text"></p>
            <button id="mi-explain-more-btn" class="btn-secondary">Explain More</button>
            <p id="mi-explain-more-output" class="hidden"></p>
            <button id="mi-next-btn" class="btn-primary"></button>
        </div>

        <div id="mi-summary-body" class="mi-page-panel glass-panel hidden">
            <h2>Interview Complete</h2>
            <p>Average score: <span id="mi-avg-score"></span>/10</p>
            <div id="mi-summary-list"></div>
            <button id="mi-restart-btn" class="btn-secondary">Try Another Mode</button>
            <button class="mi-back-btn" id="mi-back-to-domains-2">&larr; Change domain</button>
        </div>

    </main>

    <script src="/static/js/theme.js"></script>
    <script src="/static/js/auth.js"></script>
    <script src="/static/js/mock-interview.js"></script>
    <script src="/static/js/mock-interview-page.js"></script>
</body>
</html>
'@
Write-FileNoBom "frontend\mock-interview.html" $mockInterviewHtml

# ---- 7) New file: frontend/js/mock-interview-page.js ----
$mockInterviewPageJs = @'
async function miPageLoadDomains() {
    miShowPanel("mi-loading");
    try {
        const res = await authFetch("/domains/with-details");
        if (!res.ok) {
            console.error("Failed to load domains with details");
            miShowPanel("mi-domain-select");
            return;
        }
        const domains = await res.json();
        const grid = document.getElementById("mi-domain-grid");
        const empty = document.getElementById("mi-domain-empty");
        grid.innerHTML = "";

        if (!domains || domains.length === 0) {
            empty.classList.remove("hidden");
            miShowPanel("mi-domain-select");
            return;
        }
        empty.classList.add("hidden");

        domains.forEach((domain) => {
            const card = document.createElement("div");
            card.className = "mi-domain-card";
            card.innerHTML = `
                <h3>${domain.name || domain.slug}</h3>
                <p>${domain.description || ""}</p>
            `;
            card.addEventListener("click", () => {
                miState.domainSlug = domain.slug;
                miShowPanel("mi-mode-select");
            });
            grid.appendChild(card);
        });

        miShowPanel("mi-domain-select");
    } catch (e) {
        console.error("Error loading domains:", e);
        miShowPanel("mi-domain-select");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    miPageLoadDomains();

    document.querySelectorAll(".mi-mode-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            miStartInterview(btn.getAttribute("data-mode"));
        });
    });

    document.getElementById("mi-submit-btn").addEventListener("click", miSubmitAnswer);
    document.getElementById("mi-explain-more-btn").addEventListener("click", miExplainMore);
    document.getElementById("mi-next-btn").addEventListener("click", miGoNext);

    document.getElementById("mi-restart-btn").addEventListener("click", () => {
        miShowPanel("mi-mode-select");
    });

    document.getElementById("mi-back-to-domains-1").addEventListener("click", () => {
        miShowPanel("mi-domain-select");
    });
    document.getElementById("mi-back-to-domains-2").addEventListener("click", () => {
        miShowPanel("mi-domain-select");
    });
});
'@
Write-FileNoBom "frontend\js\mock-interview-page.js" $mockInterviewPageJs

# ---- 8) Append new page-layout CSS to style.css ----
$mockInterviewPageCss = @'

/* ==== Mock Interview standalone page layout (added: standalone page session) ==== */
.mi-page-container {
    max-width: 900px;
    margin: 40px auto;
    padding: 0 20px;
}
.mi-page-panel {
    padding: 32px;
    border-radius: 16px;
}
.mi-domain-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 16px;
    margin-top: 20px;
}
.mi-domain-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    cursor: pointer;
    transition: var(--transition-smooth);
}
.mi-domain-card:hover {
    border-color: var(--accent-yellow);
    transform: translateY(-2px);
}
.mi-domain-card h3 {
    margin: 0 0 8px 0;
    color: var(--text-main);
}
.mi-domain-card p {
    margin: 0;
    color: var(--text-muted);
    font-size: 0.9rem;
}
.mi-back-btn {
    background: none;
    border: none;
    color: var(--accent-primary);
    cursor: pointer;
    font-size: 0.9rem;
    margin-bottom: 16px;
    padding: 0;
}
'@
$stylePath = Join-Path $repoRoot "frontend\css\style.css"
[System.IO.File]::AppendAllText($stylePath, $mockInterviewPageCss, $utf8NoBom)
Write-Host "Appended CSS to: frontend\css\style.css"

Write-Host "`n=== DONE. Run the verification block next. ===" -ForegroundColor Green
'@