$patchScript = @'
path = "frontend/roadmap.html"
with open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

if "mock-interview.js" in content:
    print("SKIPPED: already patched")
else:
    old_scripts = '    <script src="/static/js/theme.js"></script>\r\n    <script src="/static/js/auth.js"></script>\r\n    <script src="/static/js/roadmap.js"></script>\r\n</body>'
    assert old_scripts in content, "PATCH FAILED: script tags block not found - check line endings/content"

    modal_html = '''    <div id="mock-interview-modal" class="mi-modal-overlay hidden">
        <div class="mi-modal glass-panel">
            <button id="mi-close-btn" class="mi-close" aria-label="Close">&times;</button>

            <div id="mi-mode-select">
                <h2>Start Mock Interview</h2>
                <p>Choose a mode to begin.</p>
                <div class="mi-mode-grid">
                    <button class="mi-mode-btn" data-mode="coding">Coding<span class="mi-mode-desc">AI-generated coding questions for this domain</span></button>
                    <button class="mi-mode-btn" data-mode="hr">HR / Behavioral<span class="mi-mode-desc">Soft skills, teamwork, innovation</span></button>
                    <button class="mi-mode-btn" data-mode="technical">Technical Panel<span class="mi-mode-desc">In-depth engineering interview</span></button>
                    <button class="mi-mode-btn" data-mode="mixed">Mixed<span class="mi-mode-desc">A blend of all categories</span></button>
                </div>
            </div>

            <div id="mi-interview-body" class="hidden">
                <div class="mi-progress"><span id="mi-progress-text"></span></div>
                <div class="mi-question-box">
                    <span id="mi-category-badge" class="detail-chip"></span>
                    <p id="mi-question-text"></p>
                </div>
                <textarea id="mi-answer-input" placeholder="Type your answer here..."></textarea>
                <button id="mi-submit-btn" class="btn-primary">Submit Answer</button>
            </div>

            <div id="mi-feedback-body" class="hidden">
                <div class="mi-score-circle"><span id="mi-score-value"></span><span style="font-size:0.7rem;">/10</span></div>
                <div class="mi-feedback-section">
                    <h4>Strengths</h4>
                    <ul id="mi-strengths-list"></ul>
                </div>
                <div class="mi-feedback-section">
                    <h4>Areas to improve</h4>
                    <ul id="mi-weaknesses-list"></ul>
                </div>
                <p id="mi-hint-text" class="mi-hint"></p>
                <div id="mi-explain-more-output" class="mi-explain-more-output hidden"></div>
                <div class="mi-btn-row">
                    <button id="mi-explain-more-btn" class="btn-secondary">Explain More</button>
                    <button id="mi-next-btn" class="btn-primary">Next Question</button>
                </div>
            </div>

            <div id="mi-summary-body" class="hidden">
                <h2>Interview Complete</h2>
                <div class="mi-score-circle mi-score-circle-large"><span id="mi-avg-score"></span><span style="font-size:0.8rem;">/10</span></div>
                <div id="mi-summary-list"></div>
                <button id="mi-restart-btn" class="btn-primary">Start New Interview</button>
            </div>

            <div id="mi-loading" class="mi-loading-box hidden">
                <div class="mi-spinner"></div>
                <p>Thinking...</p>
            </div>
        </div>
    </div>

    <script src="/static/js/theme.js"></script>
    <script src="/static/js/auth.js"></script>
    <script src="/static/js/roadmap.js"></script>
    <script src="/static/js/mock-interview.js"></script>
</body>'''

    content = content.replace(old_scripts, modal_html)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    print("roadmap.html patched successfully")
'@

$repoRoot = (Get-Location).Path
$scriptPath = Join-Path $repoRoot "patch_roadmap_html.py"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($scriptPath, $patchScript, $utf8NoBom)

python patch_roadmap_html.py