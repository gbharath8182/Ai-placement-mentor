let currentTopicSlug = "";
let currentProblemId = "";
let starterCodeCache = "";

document.addEventListener("DOMContentLoaded", async () => {
    // 1. Set user info in navbar
    const user = getUser();
    if (user) {
        document.getElementById("user-name").textContent = user.name;
        const expBadge = document.getElementById("user-exp-badge");
        expBadge.textContent = user.profile.experience_level;
        expBadge.className = `experience-tag exp-${user.profile.experience_level}`;
    }

    // 2. Extract slug from URL pathname (/topic/{slug})
    const pathParts = window.location.pathname.split("/");
    currentTopicSlug = pathParts[pathParts.length - 1];
    
    if (!currentTopicSlug || currentTopicSlug === "topic") {
        console.error("Invalid topic slug in URL");
        document.getElementById("topic-title").textContent = "Topic Not Found";
        return;
    }
    
    // 3. Load topic contents & problems
    await loadTopicData();
    await loadPracticeProblem();
    
    // Set up practice handlers
    document.getElementById("reset-code-btn").addEventListener("click", () => {
        if (confirm("Are you sure you want to reset your editor to the default starter code?")) {
            document.getElementById("editor").value = starterCodeCache;
        }
    });
    
    document.getElementById("run-code-btn").addEventListener("click", runCodeSubmission);
});

async function loadTopicData() {
    try {
        const res = await authFetch(`/topics/${currentTopicSlug}`);
        if (res.ok) {
            const topic = await res.json();
            
            // Set basic details
            document.getElementById("topic-title").textContent = topic.title;
            
            const diffBadge = document.getElementById("topic-difficulty-badge");
            diffBadge.textContent = topic.difficulty;
            diffBadge.className = `status-badge status-${topic.difficulty === "beginner" ? "not-started" : (topic.difficulty === "intermediate" ? "in-progress" : "completed")}`;
            
            renderContentBlocks(topic.content_blocks);
            
            // Mark topic progress as "in_progress" in background
            updateTopicProgress("in_progress");
        } else {
            document.getElementById("topic-title").textContent = "Error Loading Content";
            document.getElementById("content-blocks-area").innerHTML = `<p style="color: var(--accent-red)">Topic details could not be retrieved from the server.</p>`;
        }
    } catch (err) {
        console.error("Error loading topic:", err);
        document.getElementById("topic-title").textContent = "Connection Failure";
    }
}

function renderContentBlocks(blocks) {
    const area = document.getElementById("content-blocks-area");
    area.innerHTML = "";
    
    if (!blocks || blocks.length === 0) {
        area.innerHTML = `<p style="color: var(--text-muted)">This topic does not have any content blocks yet.</p>`;
        return;
    }
    
    blocks.forEach(block => {
        const element = document.createElement("div");
        
        if (block.type === "text") {
            element.className = "block-text";
            // Replace linebreaks with <br> for simple HTML formatting, escape HTML to avoid XSS
            const escapedVal = block.value
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
            
            // Support simple double asterisk bold formatting
            const formattedVal = escapedVal
                .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                .replace(/`(.*?)`/g, "<code style='background: var(--bg-tertiary); padding: 2px 6px; border-radius: 4px; font-family: var(--font-code); font-size: 0.9rem;'>$1</code>");
                
            element.innerHTML = formattedVal.replace(/\n/g, "<br>");
        } 
        else if (block.type === "code") {
            element.className = "block-code";
            const lang = block.language || "code";
            element.innerHTML = `
                <span class="code-lang-label">${lang}</span>
                <pre style="margin: 0;"><code class="language-${lang}">${escapeHtml(block.value)}</code></pre>
            `;
        } 
        else if (block.type === "resource_link") {
            element.innerHTML = `
                <a href="${block.url}" target="_blank" class="block-resource">
                    <span class="resource-icon">🔗</span>
                    <div style="display: flex; flex-direction: column;">
                        <span>${block.label || "External Resource"}</span>
                        <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: normal;">${block.url}</span>
                    </div>
                </a>
            `;
        }
        
        area.appendChild(element);
    });
}

async function loadPracticeProblem() {
    try {
        const res = await authFetch(`/practice/${currentTopicSlug}`);
        if (res.ok) {
            const problems = await res.json();
            
            if (problems.length > 0) {
                const problem = problems[0]; // Display the primary problem
                currentProblemId = problem.id;
                starterCodeCache = problem.starter_code;
                
                document.getElementById("problem-title").textContent = problem.title;
                document.getElementById("problem-desc").textContent = problem.description;
                document.getElementById("editor").value = problem.starter_code;
                
                const diffBadge = document.getElementById("problem-difficulty-badge");
                diffBadge.textContent = problem.difficulty;
                diffBadge.className = `problem-difficulty diff-${problem.difficulty}`;
                
                document.getElementById("practice-playground").style.display = "block";
            }
        }
    } catch (err) {
        console.error("Error fetching practice problems:", err);
    }
}

async function runCodeSubmission() {
    const code = document.getElementById("editor").value;
    const language = document.getElementById("lang-select").value;
    const runBtn = document.getElementById("run-code-btn");
    const outputPanel = document.getElementById("compiler-output");
    const container = document.getElementById("test-case-container");
    const statusTitle = document.getElementById("compiler-status-title");
    
    runBtn.textContent = "Compiling...";
    runBtn.disabled = true;
    outputPanel.style.display = "block";
    container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.9rem;">Executing code in sandboxed runtime... Please wait.</div>`;
    
    try {
        const res = await authFetch(`/practice/${currentProblemId}/run`, {
            method: "POST",
            body: { language, code }
        });
        
        if (res.ok) {
            const data = await res.json();
            container.innerHTML = "";
            
            if (data.success) {
                statusTitle.textContent = "🟢 All Test Cases Passed!";
                statusTitle.className = "compiler-output-header tc-success";
                
                // Show notification in AI sidebar that problem is solved
                if (window.appendAssistantMessage) {
                    window.appendAssistantMessage("🎉 Excellent job! You've successfully passed all compiler test cases for this topic's coding exercise. Let me know if you want to optimize your code further or take a short quiz!");
                }
            } else {
                statusTitle.textContent = "🔴 Test Cases Failed";
                statusTitle.className = "compiler-output-header tc-failed";
            }
            
            data.results.forEach(tc => {
                const tcItem = document.createElement("div");
                tcItem.className = "test-case-item";
                
                const statusIcon = tc.passed ? "✓ Passed" : "✗ Failed";
                const statusClass = tc.passed ? "tc-success" : "tc-failed";
                
                let detailsHtml = "";
                if (!tc.passed) {
                    detailsHtml = `
                        <div class="test-case-details">
                            ${tc.input ? `<div><strong>Input:</strong> ${escapeHtml(tc.input)}</div>` : ''}
                            <div><strong>Expected Output:</strong> ${escapeHtml(tc.expected)}</div>
                            <div><strong>Actual Output:</strong> ${escapeHtml(tc.actual || "[No Output]")}</div>
                            ${tc.stderr ? `<div style="color: var(--accent-red);"><strong>Stderr:</strong> ${escapeHtml(tc.stderr)}</div>` : ''}
                        </div>
                    `;
                } else {
                    detailsHtml = `
                        <div class="test-case-details" style="opacity: 0.8;">
                            ${tc.input ? `<div><strong>Input:</strong> ${escapeHtml(tc.input)}</div>` : ''}
                            <div><strong>Output:</strong> ${escapeHtml(tc.actual)}</div>
                        </div>
                    `;
                }
                
                tcItem.innerHTML = `
                    <div class="test-case-status ${statusClass}">
                        <span>${statusIcon}</span>
                        <span style="color: var(--text-muted); font-weight: normal; font-size: 0.8rem;">(Test Case #${tc.test_case_index + 1})</span>
                    </div>
                    ${detailsHtml}
                `;
                
                container.appendChild(tcItem);
            });
            
        } else {
            const err = await res.json();
            container.innerHTML = `<div style="color: var(--accent-red);">${err.detail || "Compilation error occurred."}</div>`;
        }
    } catch (err) {
        console.error("Code compile failure:", err);
        container.innerHTML = `<div style="color: var(--accent-red);">Failed to connect to execution engine. Check server link.</div>`;
    } finally {
        runBtn.textContent = "Run Solution";
        runBtn.disabled = false;
    }
}

async function updateTopicProgress(status) {
    try {
        await authFetch("/progress/update", {
            method: "POST",
            body: {
                topic_slug: currentTopicSlug,
                status: status
            }
        });
    } catch (err) {
        console.error("Error setting progress:", err);
    }
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
