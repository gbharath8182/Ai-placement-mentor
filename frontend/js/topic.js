let currentTopicSlug = "";
let currentProblemId = "";
let starterCodeCache = "";
let currentProblemTestCases = [];
let pyodideInstance = null;
let isPyodideLoading = false;

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
            
            // Render subtopics list in sidebar
            const sidebar = document.getElementById("subtopics-list-container");
            sidebar.innerHTML = "";
            
            if (topic.subtopics && topic.subtopics.length > 0) {
                topic.subtopics.forEach((sub, idx) => {
                    const item = document.createElement("div");
                    item.className = "topic-item glass-panel";
                    item.style.cssText = "padding: 10px 14px; border-radius: 8px; cursor: pointer; font-size: 0.88rem; transition: var(--transition-smooth); display: flex; align-items: center; border: 1px solid var(--border-color); color: var(--text-muted); margin-bottom: 2px;";
                    item.innerHTML = `<span style="font-weight: 500; font-family: var(--font-display); margin-right: 6px; color: var(--accent-primary);">${idx + 1}.</span> <span style="text-align: left;">${escapeHtml(sub.title)}</span>`;
                    
                    item.addEventListener("click", () => {
                        // Highlight active subtopic
                        document.querySelectorAll("#subtopics-list-container .topic-item").forEach(el => {
                            el.style.borderColor = "var(--border-color)";
                            el.style.background = "transparent";
                            el.style.color = "var(--text-muted)";
                        });
                        item.style.borderColor = "var(--accent-primary)";
                        item.style.background = "rgba(37, 99, 235, 0.05)";
                        item.style.color = "var(--text-main)";
                        
                        // Update subtopic badge & content
                        document.getElementById("subtopic-title-badge").textContent = sub.title;
                        renderContentBlocks(sub.content_blocks);
                        
                        // Trigger MathJax typeset to render any LaTeX math expressions
                        if (window.MathJax && window.MathJax.typeset) {
                            window.MathJax.typeset();
                        }
                    });
                    
                    sidebar.appendChild(item);
                });
                
                // Select the first subtopic by default
                sidebar.firstChild.click();
            } else {
                sidebar.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; padding: 10px 0;">No subtopics found.</div>`;
                document.getElementById("subtopic-title-badge").textContent = "General";
                renderContentBlocks(topic.content_blocks);
            }
            
            // Mark topic progress as "in_progress" in background
            updateTopicProgress("in_progress");
            trackActivity("lesson", 2, currentTopicSlug);
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
    
    // Separate resource_links to render at the bottom
    const contentBlocks = [];
    const resourceBlocks = [];
    blocks.forEach(block => {
        if (block.type === "resource_link") {
            resourceBlocks.push(block);
        } else {
            contentBlocks.push(block);
        }
    });
    
    contentBlocks.forEach(block => {
        const element = document.createElement("div");
        
        if (block.type === "text") {
            element.className = "block-text";
            const escapedVal = block.value
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
            
            const formattedVal = escapedVal
                .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                .replace(/`(.*?)`/g, "<code style='background: var(--bg-tertiary); padding: 2px 6px; border-radius: 4px; font-family: var(--font-code); font-size: 0.9rem;'>$1</code>");
                
            element.innerHTML = formattedVal.replace(/\n/g, "<br>");
        } 
        else if (block.type === "heading") {
            element.className = "block-heading";
            const level = block.level || 2;
            element.innerHTML = `<h${level} style="font-family: var(--font-display); color: var(--text-main); margin: 8px 0 4px 0; font-size: ${level === 2 ? '1.4rem' : '1.15rem'}; border-bottom: ${level === 2 ? '1px solid var(--border-color)' : 'none'}; padding-bottom: ${level === 2 ? '8px' : '0'};">${escapeHtml(block.value)}</h${level}>`;
        }
        else if (block.type === "divider") {
            element.innerHTML = `<hr style="border: none; border-top: 1px solid var(--border-color); margin: 12px 0;">`;
        }
        else if (block.type === "list") {
            element.className = "block-list";
            const items = block.items || [];
            const listStyle = block.ordered ? "ol" : "ul";
            element.innerHTML = `<${listStyle} style="margin: 0; padding-left: 24px; line-height: 1.9; color: var(--text-main);">${items.map(item => {
                const escaped = item.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
                    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                    .replace(/`(.*?)`/g, "<code style='background:var(--bg-tertiary);padding:2px 6px;border-radius:4px;font-family:var(--font-code);font-size:0.9rem;'>$1</code>");
                return `<li>${escaped}</li>`;
            }).join("")}</${listStyle}>`;
        }
        else if (block.type === "callout") {
            const colors = { tip: "var(--accent-green)", warning: "var(--accent-yellow)", info: "var(--accent-primary)", important: "var(--accent-secondary)" };
            const icons = { tip: "💡", warning: "⚠️", info: "ℹ️", important: "📌" };
            const kind = block.kind || "info";
            const borderColor = colors[kind] || colors.info;
            element.innerHTML = `<div style="border-left: 4px solid ${borderColor}; background: rgba(255,255,255,0.03); padding: 14px 18px; border-radius: 0 8px 8px 0; margin: 4px 0;">
                <strong style="color: ${borderColor};">${icons[kind] || ""} ${(block.title || kind).toUpperCase()}</strong>
                <p style="margin: 6px 0 0 0; color: var(--text-main); line-height: 1.7;">${escapeHtml(block.value).replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/`(.*?)`/g, "<code style='background:var(--bg-tertiary);padding:2px 6px;border-radius:4px;font-family:var(--font-code);font-size:0.9rem;'>$1</code>").replace(/\n/g, "<br>")}</p>
            </div>`;
        }
        else if (block.type === "code") {
            element.className = "block-code";
            const lang = block.language || "code";
            element.innerHTML = `
                <span class="code-lang-label">${lang}</span>
                <pre style="margin: 0;"><code class="language-${lang}">${escapeHtml(block.value)}</code></pre>
            `;
        }
        else if (block.type === "diagram") {
            element.className = "concept-diagram";
            const title = document.createElement("h3");
            title.textContent = block.title || "Concept map";
            const diagram = document.createElement("pre");
            diagram.className = "mermaid";
            diagram.textContent = block.value || "";
            element.append(title, diagram);
        }
        else if (block.type === "knowledge_check") {
            element.className = "knowledge-check";
            const question = document.createElement("p");
            question.className = "knowledge-question";
            question.textContent = block.question || "Quick check";
            const answers = document.createElement("div");
            answers.className = "knowledge-options";
            (block.options || []).forEach((option, index) => {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "knowledge-option";
                button.textContent = option;
                button.addEventListener("click", () => {
                    answers.querySelectorAll("button").forEach(item => item.disabled = true);
                    button.classList.add(index === block.correct_index ? "is-correct" : "is-incorrect");
                    const result = document.createElement("p");
                    result.className = "knowledge-result";
                    result.textContent = index === block.correct_index
                        ? `Correct — ${block.explanation || ""}`
                        : `Not quite — ${block.explanation || ""}`;
                    answers.after(result);
                }, { once: true });
                answers.appendChild(button);
            });
            const label = document.createElement("span");
            label.className = "knowledge-label";
            label.textContent = "Active recall checkpoint";
            element.append(label, question, answers);
        }
        
        area.appendChild(element);
    });

    if (window.mermaid) {
        window.mermaid.initialize({ startOnLoad: false, theme: document.documentElement.classList.contains("light-theme") ? "default" : "dark", securityLevel: "strict" });
        window.mermaid.run({ nodes: area.querySelectorAll(".mermaid") }).catch((error) => console.error("Diagram render error:", error));
    }
    
    // Render resource links in a grouped section at the bottom
    if (resourceBlocks.length > 0) {
        const refSection = document.createElement("div");
        refSection.style.cssText = "margin-top: 40px; border-top: 1px solid var(--border-color); padding-top: 20px;";
        refSection.innerHTML = `<h3 style="font-family: var(--font-display); color: var(--text-muted); font-size: 1rem; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 1px;">📚 References & Recommended Reading</h3>`;
        
        resourceBlocks.forEach(block => {
            const linkEl = document.createElement("div");
            linkEl.innerHTML = `
                <a href="${block.url}" target="_blank" class="block-resource">
                    <span class="resource-icon">🔗</span>
                    <div style="display: flex; flex-direction: column;">
                        <span>${block.label || "External Resource"}</span>
                        <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: normal;">${block.url}</span>
                    </div>
                </a>
            `;
            refSection.appendChild(linkEl);
        });
        
        area.appendChild(refSection);
    }
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
                currentProblemTestCases = problem.test_cases || [];
                
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
    
    runBtn.textContent = "Running...";
    runBtn.disabled = true;
    outputPanel.style.display = "block";
    container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.9rem;">Executing code in browser sandbox...</div>`;
    
    try {
        let testCases = currentProblemTestCases;
        if (!testCases || testCases.length === 0) {
            testCases = [{ input: "", expected_output: "" }];
        }
        
        let results = [];
        let overallPassed = true;
        
        if (language === "python") {
            if (!pyodideInstance) {
                if (isPyodideLoading) return;
                isPyodideLoading = true;
                container.innerHTML = `<div style="color: var(--accent-primary); font-size: 0.9rem;">Initializing Pyodide WebAssembly runtime (approx 5-10s)...</div>`;
                pyodideInstance = await loadPyodide();
                
                // Set up Mock Stdin helper once loaded
                await pyodideInstance.runPythonAsync(`
import sys
import io
import builtins

class MockStdin:
    def __init__(self, data=""):
        self.data = data
        self.lines = data.split('\\n')
        self.index = 0
    def readline(self):
        if self.index < len(self.lines):
            val = self.lines[self.index]
            self.index += 1
            return val + '\\n'
        return ''
    def read(self):
        return self.data

def set_mock_stdin(data):
    sys.stdin = MockStdin(data)
    builtins.input = lambda prompt="": sys.stdin.readline().rstrip('\\r\\n')
`);
                isPyodideLoading = false;
            }
            
            for (let idx = 0; idx < testCases.length; idx++) {
                const tc = testCases[idx];
                let tcOutput = "";
                let tcError = "";
                
                const stdoutDecoder = new TextDecoder();
                const stderrDecoder = new TextDecoder();
                pyodideInstance.setStdout({
                    write: (buf) => {
                        tcOutput += stdoutDecoder.decode(buf, { stream: true });
                        return buf.length;
                    }
                });
                pyodideInstance.setStderr({
                    write: (buf) => {
                        tcError += stderrDecoder.decode(buf, { stream: true });
                        return buf.length;
                    }
                });
                
                try {
                    // Set the mock stdin for this test case
                    // Safely escape inputs
                    const escapedInput = tc.input.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
                    await pyodideInstance.runPythonAsync(`set_mock_stdin("${escapedInput}")`);
                    
                    // Run user code
                    await pyodideInstance.runPythonAsync(code);
                    
                    const expected = tc.expected_output.trim().replace(/\r\n/g, "\n");
                    const actual = tcOutput.trim().replace(/\r\n/g, "\n");
                    const passed = (actual === expected) && !tcError;
                    
                    if (!passed) overallPassed = false;
                    
                    results.push({
                        test_case_index: idx,
                        input: tc.input,
                        expected: tc.expected_output,
                        actual: tcOutput,
                        stderr: tcError,
                        passed: passed
                    });
                } catch (err) {
                    overallPassed = false;
                    results.push({
                        test_case_index: idx,
                        input: tc.input,
                        expected: tc.expected_output,
                        actual: tcOutput,
                        stderr: err.message,
                        passed: false
                    });
                }
            }
        } 
        else if (language === "javascript") {
            for (let idx = 0; idx < testCases.length; idx++) {
                const tc = testCases[idx];
                let tcOutput = "";
                let tcError = "";
                
                const originalLog = console.log;
                const originalError = console.error;
                
                console.log = (...args) => {
                    tcOutput += args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(" ") + "\n";
                };
                console.error = (...args) => {
                    tcError += args.join(" ") + "\n";
                };
                
                try {
                    // Mock simple prompt/input lines for JavaScript
                    window.prompt = () => {
                        if (!window.__js_stdin_lines) {
                            window.__js_stdin_lines = tc.input.split('\n');
                            window.__js_stdin_idx = 0;
                        }
                        if (window.__js_stdin_idx < window.__js_stdin_lines.length) {
                            return window.__js_stdin_lines[window.__js_stdin_idx++];
                        }
                        return "";
                    };
                    window.__js_stdin_lines = tc.input.split('\n');
                    window.__js_stdin_idx = 0;
                    
                    new Function(code)();
                    
                    const expected = tc.expected_output.trim().replace(/\r\n/g, "\n");
                    const actual = tcOutput.trim().replace(/\r\n/g, "\n");
                    const passed = (actual === expected) && !tcError;
                    
                    if (!passed) overallPassed = false;
                    
                    results.push({
                        test_case_index: idx,
                        input: tc.input,
                        expected: tc.expected_output,
                        actual: tcOutput,
                        stderr: tcError,
                        passed: passed
                    });
                } catch (err) {
                    overallPassed = false;
                    results.push({
                        test_case_index: idx,
                        input: tc.input,
                        expected: tc.expected_output,
                        actual: tcOutput,
                        stderr: err.message,
                        passed: false
                    });
                } finally {
                    console.log = originalLog;
                    console.error = originalError;
                }
            }
        }
        
        container.innerHTML = "";
        
        if (overallPassed) {
            statusTitle.textContent = "🟢 All Test Cases Passed!";
            statusTitle.className = "compiler-output-header tc-success";
            
            // Call the completed endpoint to save progress
            const res = await authFetch(`/practice/${currentProblemId}/completed`, {
                method: "POST"
            });
            if (res.ok) {
                console.log("Database updated: topic marked as completed.");
            }
            
            // Show notification in AI sidebar that problem is solved
            if (window.appendAssistantMessage) {
                window.appendAssistantMessage("🎉 Excellent job! You've successfully passed all compiler test cases for this topic's coding exercise. Let me know if you want to optimize your code further or take a short quiz!");
            }
        } else {
            statusTitle.textContent = "🔴 Test Cases Failed";
            statusTitle.className = "compiler-output-header tc-failed";
        }
        
        results.forEach(tc => {
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
                        ${tc.stderr ? `<div style="color: var(--accent-red);"><strong>Error/Stderr:</strong> ${escapeHtml(tc.stderr)}</div>` : ''}
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
        
    } catch (err) {
        console.error("Local compile execution error:", err);
        container.innerHTML = `<div style="color: var(--accent-red);">Execution error occurred in local sandbox: ${err.message}</div>`;
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

