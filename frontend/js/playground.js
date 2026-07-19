let pyodideInstance = null;
let isPyodideLoading = false;
let currentLang = "python";

const templates = {
    python: `# stdin is provided per test case\nname = input().strip() or "Placement Mentor"\nprint(f"Hello, {name}!")\n`,
    javascript: `// prompt() returns one input line per test case\nconst name = prompt() || "Placement Mentor";\nconsole.log(\`Hello, \${name}!\`);\n`
};

const cachedCode = { python: templates.python, javascript: templates.javascript };
let testCases = [
    { input: "Asha", expected_output: "Hello, Asha!" },
    { input: "", expected_output: "Hello, Placement Mentor!" }
];

document.addEventListener("DOMContentLoaded", () => {
    hydrateUser();
    const editor = document.getElementById("playground-editor");
    const langSelect = document.getElementById("playground-lang-select");
    const themeSelect = document.getElementById("playground-theme-select");
    const runBtn = document.getElementById("playground-run-btn");
    const resetBtn = document.getElementById("playground-reset-btn");
    const clearBtn = document.getElementById("playground-clear-btn");
    const addBtn = document.getElementById("add-testcase-btn");

    editor.value = cachedCode[currentLang];
    applyEditorTheme(themeSelect.value);
    renderTestCases();

    langSelect.addEventListener("change", event => {
        cachedCode[currentLang] = editor.value;
        currentLang = event.target.value;
        editor.value = cachedCode[currentLang];
        setStatus(currentLang === "python" && !pyodideInstance ? "Pyodide will load on first run" : "Ready");
    });

    themeSelect.addEventListener("change", event => applyEditorTheme(event.target.value));
    resetBtn.addEventListener("click", () => {
        if (!confirm(`Reset editor to default ${currentLang} starter code?`)) return;
        editor.value = templates[currentLang];
        cachedCode[currentLang] = templates[currentLang];
    });
    clearBtn.addEventListener("click", () => {
        document.getElementById("playground-console").textContent = "Console cleared.";
        document.getElementById("results-body").innerHTML = "";
    });
    addBtn.addEventListener("click", () => {
        testCases.push({ input: "", expected_output: "" });
        renderTestCases();
    });
    runBtn.addEventListener("click", runAllTests);
});

function hydrateUser() {
    const user = getUser();
    if (!user) return;
    document.getElementById("user-name").textContent = user.name;
    const badge = document.getElementById("user-exp-badge");
    badge.textContent = user.profile.experience_level;
    badge.className = `experience-tag exp-${user.profile.experience_level}`;
}

function renderTestCases() {
    document.getElementById("testcase-list").innerHTML = testCases.map((testCase, index) => `
        <div class="testcase-row">
            <label>Input<textarea data-index="${index}" data-field="input">${escapeHtml(testCase.input)}</textarea></label>
            <label>Expected<textarea data-index="${index}" data-field="expected_output">${escapeHtml(testCase.expected_output)}</textarea></label>
            <button class="btn-secondary testcase-remove" data-index="${index}" aria-label="Remove test case">x</button>
        </div>
    `).join("");

    document.querySelectorAll("#testcase-list textarea").forEach(textarea => {
        textarea.addEventListener("input", event => {
            const index = Number(event.target.dataset.index);
            testCases[index][event.target.dataset.field] = event.target.value;
        });
    });
    document.querySelectorAll(".testcase-remove").forEach(button => {
        button.addEventListener("click", event => {
            if (testCases.length === 1) return;
            testCases.splice(Number(event.target.dataset.index), 1);
            renderTestCases();
        });
    });
}

async function runAllTests() {
    const runBtn = document.getElementById("playground-run-btn");
    const code = document.getElementById("playground-editor").value;
    runBtn.disabled = true;
    setStatus("Running tests...");
    document.getElementById("playground-console").textContent = "";

    const results = [];
    for (const [index, testCase] of testCases.entries()) {
        const result = currentLang === "python"
            ? await runPython(code, testCase.input)
            : await runJavaScript(code, testCase.input);
        result.caseNumber = index + 1;
        result.expected = normalizeOutput(testCase.expected_output);
        result.passed = result.ok && normalizeOutput(result.output) === result.expected;
        results.push(result);
    }

    renderResults(results);
    document.getElementById("playground-console").textContent = results.map(result => `Case ${result.caseNumber}: ${result.output || result.error || "[no output]"}`).join("\n\n");
    setStatus(results.every(result => result.passed) ? "All tests passed" : "Review failed cases");
    runBtn.disabled = false;
    trackActivity("playground", Math.max(1, testCases.length));
}

async function ensurePyodide() {
    if (pyodideInstance) return pyodideInstance;
    if (isPyodideLoading) return null;
    isPyodideLoading = true;
    setStatus("Loading Pyodide runtime...");
    pyodideInstance = await loadPyodide();
    isPyodideLoading = false;
    return pyodideInstance;
}

async function runPython(code, input) {
    try {
        const pyodide = await ensurePyodide();
        if (!pyodide) return { ok: false, output: "", error: "Runtime loading", type: "runtime" };
        let output = "";
        const stdoutDecoder = new TextDecoder();
        const stderrDecoder = new TextDecoder();
        pyodide.setStdout({ write: buf => { output += stdoutDecoder.decode(buf, { stream: true }); return buf.length; } });
        pyodide.setStderr({ write: buf => { output += stderrDecoder.decode(buf, { stream: true }); return buf.length; } });
        pyodide.globals.set("__codex_input_lines", input.split(/\r?\n/));
        await pyodide.runPythonAsync(`
import builtins
__codex_input_iter = iter(__codex_input_lines)
builtins.input = lambda prompt='': next(__codex_input_iter, '')
`);
        await pyodide.runPythonAsync(code);
        return { ok: true, output: normalizeOutput(output), error: "", type: "pass" };
    } catch (err) {
        return classifyError(err);
    }
}

async function runJavaScript(code, input) {
    const lines = input.split(/\r?\n/);
    let cursor = 0;
    let output = "";
    const originalLog = console.log;
    const originalError = console.error;
    try {
        console.log = (...args) => { output += args.join(" ") + "\n"; };
        console.error = (...args) => { output += args.join(" ") + "\n"; };
        new Function("prompt", code)(() => lines[cursor++] || "");
        return { ok: true, output: normalizeOutput(output), error: "", type: "pass" };
    } catch (err) {
        return classifyError(err);
    } finally {
        console.log = originalLog;
        console.error = originalError;
    }
}

function classifyError(err) {
    const message = err && err.message ? err.message : String(err);
    const type = /syntax|invalid/i.test(message) ? "syntax" : /memory|allocation/i.test(message) ? "mle" : /timeout|time/i.test(message) ? "tle" : "runtime";
    return { ok: false, output: "", error: message, type };
}

function renderResults(results) {
    document.getElementById("results-body").innerHTML = results.map(result => `
        <tr>
            <td>#${result.caseNumber}</td>
            <td><span class="error-badge ${result.passed ? "badge-pass" : `badge-${result.type}`}">${result.passed ? "pass" : result.type}</span></td>
            <td><code>${escapeHtml(result.expected)}</code></td>
            <td><code>${escapeHtml(result.output || result.error)}</code></td>
        </tr>
    `).join("");
}

function applyEditorTheme(theme) {
    document.getElementById("playground-editor").className = `editor-textarea editor-theme-${theme}`;
}

function setStatus(text) {
    document.getElementById("playground-status").textContent = text;
}

function normalizeOutput(value) {
    return String(value || "").replace(/\r/g, "").trim();
}

function escapeHtml(text) {
    return String(text || "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}


