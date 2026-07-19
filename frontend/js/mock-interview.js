let miState = {
    domainSlug: null,
    sessionId: null,
    pendingNext: null,
    lastDone: false
};

function miEl(id) {
    return document.getElementById(id);
}

function miShowPanel(panelId) {
    ["mi-domain-select", "mi-mode-select", "mi-interview-body", "mi-feedback-body", "mi-summary-body", "mi-loading"].forEach((id) => {
        const el = miEl(id);
        if (el) el.classList.toggle("hidden", id !== panelId);
    });
}

window.openMockInterviewModal = function (domainSlug) {
    miState = { domainSlug: domainSlug, sessionId: null, pendingNext: null, lastDone: false };
    miEl("mock-interview-modal").classList.remove("hidden");
    miShowPanel("mi-mode-select");
};

function closeMockInterviewModal() {
    miEl("mock-interview-modal").classList.add("hidden");
}

async function miStartInterview(mode) {
    miShowPanel("mi-loading");
    try {
        const res = await authFetch("/mock-interview/start", {
            method: "POST",
            body: {
                domain_slug: miState.domainSlug,
                mode: mode,
                num_questions: 5
            }
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            alert("Could not start interview: " + (err.detail || "Server error"));
            miShowPanel("mi-mode-select");
            return;
        }
        const data = await res.json();
        miState.sessionId = data.session_id;
        miRenderQuestion(data);
    } catch (e) {
        console.error("Mock interview start error:", e);
        alert("Connection error starting interview.");
        miShowPanel("mi-mode-select");
    }
}

function miRenderQuestion(data) {
    miEl("mi-progress-text").textContent = `Question ${data.question_number} of ${data.total_questions}`;
    miEl("mi-category-badge").textContent = `${data.category} · ${data.difficulty || "intermediate"}`;
    miEl("mi-question-text").textContent = data.question;
    miEl("mi-answer-input").value = "";
    miEl("mi-explain-more-output").classList.add("hidden");
    miEl("mi-explain-more-output").textContent = "";
    miShowPanel("mi-interview-body");
}

async function miSubmitAnswer() {
    const answer = miEl("mi-answer-input").value.trim();
    if (!answer) {
        alert("Please type an answer before submitting.");
        return;
    }
    miShowPanel("mi-loading");
    try {
        const res = await authFetch("/mock-interview/answer", {
            method: "POST",
            body: {
                session_id: miState.sessionId,
                answer: answer
            }
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            alert("Could not submit answer: " + (err.detail || "Server error"));
            miShowPanel("mi-interview-body");
            return;
        }
        const data = await res.json();
        miState.lastDone = data.done;
        miState.pendingNext = data.done ? null : {
            question_number: data.question_number,
            total_questions: data.total_questions,
            category: data.category,
            difficulty: data.difficulty,
            question: data.question
        };
        miState.pendingSummary = data.summary || null;
        miRenderFeedback(data.feedback);
    } catch (e) {
        console.error("Mock interview answer error:", e);
        alert("Connection error submitting answer.");
        miShowPanel("mi-interview-body");
    }
}

function miRenderFeedback(feedback) {
    miEl("mi-score-value").textContent = feedback.score;

    const strengthsList = miEl("mi-strengths-list");
    strengthsList.innerHTML = "";
    (feedback.strengths || []).forEach((s) => {
        const li = document.createElement("li");
        li.textContent = s;
        strengthsList.appendChild(li);
    });
    if ((feedback.strengths || []).length === 0) {
        strengthsList.innerHTML = "<li>None noted.</li>";
    }

    const weaknessesList = miEl("mi-weaknesses-list");
    weaknessesList.innerHTML = "";
    (feedback.weaknesses || []).forEach((w) => {
        const li = document.createElement("li");
        li.textContent = w;
        weaknessesList.appendChild(li);
    });
    if ((feedback.weaknesses || []).length === 0) {
        weaknessesList.innerHTML = "<li>None noted.</li>";
    }

    miEl("mi-hint-text").textContent = feedback.model_answer_hint || "";
    miEl("mi-next-btn").textContent = miState.lastDone ? "View Summary" : "Next Question";
    miShowPanel("mi-feedback-body");
}

async function miExplainMore() {
    const btn = miEl("mi-explain-more-btn");
    btn.disabled = true;
    btn.textContent = "Loading...";
    try {
        const res = await authFetch("/mock-interview/explain-more", {
            method: "POST",
            body: { session_id: miState.sessionId }
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            alert("Could not fetch explanation: " + (err.detail || "Server error"));
            return;
        }
        const data = await res.json();
        const out = miEl("mi-explain-more-output");
        out.innerHTML = (typeof marked !== "undefined")
            ? marked.parse(data.explanation)
            : data.explanation;
        out.classList.add("mi-markdown-body");
        out.classList.remove("hidden");
    } catch (e) {
        console.error("Explain more error:", e);
        alert("Connection error fetching explanation.");
    } finally {
        btn.disabled = false;
        btn.textContent = "Explain More";
    }
}

function miGoNext() {
    if (miState.lastDone) {
        miRenderSummary(miState.pendingSummary);
    } else if (miState.pendingNext) {
        miRenderQuestion(miState.pendingNext);
    }
}

function miRenderSummary(summary) {
    if (!summary) {
        miShowPanel("mi-mode-select");
        return;
    }
    miEl("mi-avg-score").textContent = summary.average_score;
    const list = miEl("mi-summary-list");
    list.innerHTML = "";
    (summary.per_question || []).forEach((item, i) => {
        const div = document.createElement("div");
        div.className = "mi-summary-item";
        div.innerHTML = `
            <div class="mi-summary-item-head">
                <span>Q${i + 1} - ${item.category} · ${item.difficulty || "intermediate"}</span>
                <strong>${item.score}/10</strong>
            </div>
            <p style="font-size:0.85rem; color: var(--text-muted);">${item.question}</p>
        `;
        list.appendChild(div);
    });
    miShowPanel("mi-summary-body");
}

document.addEventListener("DOMContentLoaded", () => {
    const modal = miEl("mock-interview-modal");
    if (!modal) return;

    miEl("mi-close-btn").addEventListener("click", closeMockInterviewModal);

    document.querySelectorAll(".mi-mode-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            miStartInterview(btn.getAttribute("data-mode"));
        });
    });

    miEl("mi-submit-btn").addEventListener("click", miSubmitAnswer);
    miEl("mi-explain-more-btn").addEventListener("click", miExplainMore);
    miEl("mi-next-btn").addEventListener("click", miGoNext);
    miEl("mi-restart-btn").addEventListener("click", () => {
        miShowPanel("mi-mode-select");
    });
});
