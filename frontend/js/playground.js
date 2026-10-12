let currentLang = "python";
const templates = {
    python: 'name = input().strip() or "Placement Mentor"\nprint(f"Hello, {name}!")\n',
    javascript: 'const name = prompt() || "Placement Mentor";\nconsole.log(`Hello, ${name}!`);\n'
};
const cachedCode = { ...templates };
let testCases = [{ input: "Asha", expected_output: "Hello, Asha!" }, { input: "", expected_output: "Hello, Placement Mentor!" }];

document.addEventListener("DOMContentLoaded", () => {
    const user = getUser();
    if (user) {
        document.getElementById("user-name").textContent = user.name;
        document.getElementById("user-exp-badge").textContent = user.profile?.experience_level || "fresher";
    }
    const editor = document.getElementById("playground-editor");
    const language = document.getElementById("playground-lang-select");
    const theme = document.getElementById("playground-theme-select");
    editor.value = cachedCode[currentLang];
    renderTestCases();
    applyEditorTheme(theme.value);
    language.addEventListener("change", event => {
        cachedCode[currentLang] = editor.value;
        currentLang = event.target.value;
        editor.value = cachedCode[currentLang];
        setStatus("Ready for remote execution");
    });
    theme.addEventListener("change", event => applyEditorTheme(event.target.value));
    document.getElementById("playground-reset-btn").addEventListener("click", () => {
        if (confirm(`Reset to default ${currentLang} starter code?`)) editor.value = templates[currentLang];
    });
    document.getElementById("playground-clear-btn").addEventListener("click", () => {
        document.getElementById("playground-console").textContent = "Console cleared.";
        document.getElementById("results-body").replaceChildren();
    });
    document.getElementById("add-testcase-btn").addEventListener("click", () => {
        if (testCases.length >= 20) { setStatus("A run supports up to 20 test cases."); return; }
        testCases.push({ input: "", expected_output: "" });
        renderTestCases();
    });
    document.getElementById("playground-run-btn").addEventListener("click", runAllTests);
});

function renderTestCases() {
    const container = document.getElementById("testcase-list");
    container.replaceChildren();
    testCases.forEach((testCase, index) => {
        const row = document.createElement("div");
        row.className = "testcase-row";
        [["input", "Input"], ["expected_output", "Expected output"]].forEach(([field, title]) => {
            const label = document.createElement("label");
            label.textContent = title;
            const textarea = document.createElement("textarea");
            textarea.value = testCase[field];
            textarea.maxLength = 16384;
            textarea.addEventListener("input", () => { testCases[index][field] = textarea.value; });
            label.appendChild(textarea);
            row.appendChild(label);
        });
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "btn-secondary testcase-remove";
        remove.textContent = "Remove";
        remove.setAttribute("aria-label", `Remove test case ${index + 1}`);
        remove.disabled = testCases.length === 1;
        remove.addEventListener("click", () => { testCases.splice(index, 1); renderTestCases(); });
        row.appendChild(remove);
        container.appendChild(row);
    });
}

async function runAllTests() {
    const button = document.getElementById("playground-run-btn");
    if (button.disabled) return;
    button.disabled = true;
    setStatus("Running in the remote sandbox…");
    document.getElementById("playground-console").textContent = "";
    try {
        const response = await authFetch("/practice/run", { method: "POST", body: { language: currentLang, code: document.getElementById("playground-editor").value, test_cases: testCases } });
        const payload = await response.json();
        if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Execution is unavailable. Please retry.");
        renderResults(payload.results);
        document.getElementById("playground-console").textContent = payload.results.map((result, index) => `Case ${index + 1}: ${result.actual || result.stderr || "[no output]"}`).join("\n\n");
        setStatus(payload.results.every(result => result.passed) ? "All tests passed · exploratory practice" : "Review failed cases");
        trackActivity("playground", 1);
    } catch (error) { setStatus(error.message); }
    finally { button.disabled = false; }
}

function renderResults(results) {
    const table = document.getElementById("results-body");
    table.replaceChildren();
    results.forEach((result, index) => {
        const row = document.createElement("tr");
        [`#${index + 1}`, result.passed ? "Passed" : "Failed", result.expected, result.actual || result.stderr || "[no output]"].forEach(value => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        });
        table.appendChild(row);
    });
}

function applyEditorTheme(theme) {
    document.getElementById("playground-editor").className = `editor-textarea editor-theme-${theme}`;
}

function setStatus(text) {
    document.getElementById("playground-status").textContent = text;
}
