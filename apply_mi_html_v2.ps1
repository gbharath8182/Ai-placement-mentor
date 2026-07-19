$ErrorActionPreference = "Stop"
$repoRoot = (Get-Location).Path
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$html = @'
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
            <div id="mi-domain-grid-wrap">
                <h1>Mock Interview</h1>
                <p>Pick a domain to start a practice interview.</p>
                <div id="mi-domain-grid" class="mi-domain-grid"></div>
                <p id="mi-domain-empty" class="hidden" style="color: var(--text-muted);">
                    No domains with interview content yet. Check back soon.
                </p>
            </div>

            <div id="mi-mode-grid-wrap" class="hidden">
                <button class="mi-back-link" id="mi-back-to-domains">&larr; Change domain</button>
                <h2>Choose a Mode</h2>
                <p>Select how you want to be interviewed.</p>
                <div class="mi-mode-grid">
                    <button class="mi-mode-btn" data-mode="coding">Coding<span class="mi-mode-desc">AI-generated coding questions for this domain</span></button>
                    <button class="mi-mode-btn" data-mode="hr">HR / Behavioral<span class="mi-mode-desc">Soft skills, teamwork, innovation</span></button>
                    <button class="mi-mode-btn" data-mode="technical">Technical Panel<span class="mi-mode-desc">In-depth engineering interview</span></button>
                    <button class="mi-mode-btn" data-mode="mixed">Mixed<span class="mi-mode-desc">A bit of everything</span></button>
                </div>
            </div>
        </div>

        <div id="mi-interview-body" class="mi-page-panel glass-panel hidden">
            <p id="mi-progress-text"></p>
            <span id="mi-category-badge"></span>
            <h3 id="mi-question-text"></h3>
            <textarea id="mi-answer-input" rows="8" placeholder="Type your answer..."></textarea>
            <button id="mi-submit-btn" class="btn-primary">Submit Answer</button>
            <div class="mi-end-interview-row">
                <button id="mi-end-btn">End Interview Now &amp; See Score</button>
            </div>
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
            <div class="mi-summary-actions">
                <button id="mi-restart-btn" class="btn-secondary">Try Another Mode (Same Domain)</button>
                <button id="mi-new-domain-btn" class="btn-secondary">Pick a Different Domain</button>
            </div>
        </div>

    </main>

    <script src="/static/js/theme.js"></script>
    <script src="/static/js/auth.js"></script>
    <script src="/static/js/mock-interview.js"></script>
    <script src="/static/js/mock-interview-page.js"></script>
</body>
</html>
'@

$target = Join-Path $repoRoot "frontend\mock-interview.html"
[System.IO.File]::WriteAllText($target, $html, $utf8NoBom)
Write-Host "Rewrote: frontend\mock-interview.html"