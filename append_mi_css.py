path = "frontend/css/style.css"
with open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

marker = ".mi-modal-overlay"
if marker in content:
    print("SKIPPED: mock-interview CSS already present, not duplicating")
else:
    addition = '''
/* ===== Mock Interview Modal ===== */
.mi-modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(3, 6, 12, 0.75);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.mi-modal-overlay.hidden {
    display: none;
}

.mi-modal {
    position: relative;
    width: min(560px, 92vw);
    max-height: 86vh;
    overflow-y: auto;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    box-shadow: var(--shadow-premium);
    padding: 28px;
}

.mi-close {
    position: absolute;
    top: 14px;
    right: 16px;
    background: none;
    border: none;
    color: var(--text-muted);
    font-size: 1.5rem;
    cursor: pointer;
    line-height: 1;
}

.mi-close:hover {
    color: var(--text-main);
}

.mi-modal h2 {
    font-family: var(--font-display);
    margin-bottom: 6px;
}

.mi-modal > p {
    color: var(--text-muted);
    margin-bottom: 18px;
}

.mi-mode-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.mi-mode-btn {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px 12px;
    color: var(--text-main);
    font-family: var(--font-sans);
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: var(--transition-smooth);
    text-align: left;
}

.mi-mode-btn:hover {
    border-color: var(--accent-primary);
    transform: translateY(-2px);
}

.mi-mode-btn span.mi-mode-desc {
    display: block;
    font-weight: 400;
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 4px;
}

.mi-progress {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 10px;
}

.mi-question-box {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 14px;
}

.mi-question-box p {
    color: var(--text-main);
    line-height: 1.6;
    margin-top: 8px;
}

#mi-answer-input {
    width: 100%;
    min-height: 120px;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    color: var(--text-main);
    font-family: var(--font-sans);
    padding: 12px;
    resize: vertical;
    margin-bottom: 14px;
}

#mi-answer-input:focus {
    outline: none;
    border-color: var(--accent-primary);
}

.mi-score-circle {
    width: 84px;
    height: 84px;
    border-radius: 50%;
    background: var(--grad-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    color: #0d1117;
    font-family: var(--font-display);
    font-weight: 700;
    margin: 0 auto 18px auto;
}

.mi-score-circle-large {
    width: 110px;
    height: 110px;
    font-size: 1.1rem;
}

#mi-score-value {
    font-size: 1.6rem;
    line-height: 1;
}

.mi-feedback-section {
    margin-bottom: 12px;
}

.mi-feedback-section h4 {
    font-size: 0.9rem;
    color: var(--text-main);
    margin-bottom: 6px;
}

.mi-feedback-section ul {
    list-style: none;
    padding: 0;
}

.mi-feedback-section li {
    color: var(--text-muted);
    font-size: 0.88rem;
    line-height: 1.5;
    padding-left: 16px;
    position: relative;
    margin-bottom: 4px;
}

.mi-feedback-section li::before {
    content: "\2022";
    position: absolute;
    left: 0;
    color: var(--accent-primary);
}

.mi-hint {
    background: rgba(88, 166, 255, 0.06);
    border-left: 2px solid var(--accent-primary);
    padding: 10px 12px;
    border-radius: 0 6px 6px 0;
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-bottom: 16px;
}

.mi-explain-more-output {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 14px;
    margin: 12px 0;
    color: var(--text-muted);
    font-size: 0.88rem;
    line-height: 1.6;
}

.mi-summary-item {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
}

.mi-summary-item-head {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 4px;
}

.mi-summary-item-head strong {
    color: var(--text-main);
}

.mi-loading-box {
    text-align: center;
    padding: 30px 0;
    color: var(--text-muted);
}

.mi-spinner {
    width: 34px;
    height: 34px;
    border: 3px solid var(--border-color);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    margin: 0 auto 12px auto;
    animation: mi-spin 0.8s linear infinite;
}

@keyframes mi-spin {
    to { transform: rotate(360deg); }
}

.mi-btn-row {
    display: flex;
    gap: 10px;
    margin-top: 6px;
}

.mi-btn-row .btn-primary,
.mi-btn-row .btn-secondary {
    width: auto;
    flex: 1;
}

.mi-start-btn {
    width: auto;
    padding: 10px 20px;
    margin-top: 10px;
    display: inline-block;
}'''
    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write(addition)
    print("CSS appended successfully")