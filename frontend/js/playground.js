let pyodideInstance = null;
let isPyodideLoading = false;

// Starter templates
const templates = {
    python: `# Write Python code here...
print("Hello from the Python Playground!")
x = [i**2 for i in range(5)]
print(f"Squares list: {x}")
`,
    javascript: `// Write JavaScript code here...
console.log("Hello from the JavaScript Playground!");
const x = Array.from({length: 5}, (_, i) => i**2);
console.log(\`Squares list: \${x.join(', ')}\`);
`
};

let cachedCode = {
    python: templates.python,
    javascript: templates.javascript
};

let currentLang = "python";

document.addEventListener("DOMContentLoaded", () => {
    // 1. Populate navbar user info
    const user = getUser();
    if (user) {
        document.getElementById("user-name").textContent = user.name;
        const expBadge = document.getElementById("user-exp-badge");
        expBadge.textContent = user.profile.experience_level;
        expBadge.className = `experience-tag exp-\${user.profile.experience_level}`;
    }

    const editor = document.getElementById("playground-editor");
    const langSelect = document.getElementById("playground-lang-select");
    const runBtn = document.getElementById("playground-run-btn");
    const resetBtn = document.getElementById("playground-reset-btn");
    const clearBtn = document.getElementById("playground-clear-btn");
    const consoleDiv = document.getElementById("playground-console");
    const statusText = document.getElementById("playground-status");

    // Initialize editor content
    editor.value = cachedCode[currentLang];

    // Language select change handler
    langSelect.addEventListener("change", (e) => {
        // Save current code to cache
        cachedCode[currentLang] = editor.value;
        
        currentLang = e.target.value;
        editor.value = cachedCode[currentLang];
        
        if (currentLang === "python") {
            statusText.textContent = pyodideInstance ? "Ready" : "Pyodide will load on first run";
        } else {
            statusText.textContent = "Ready";
        }
    });

    // Reset button handler
    resetBtn.addEventListener("click", () => {
        if (confirm("Reset editor to default starter code for " + currentLang + "?")) {
            editor.value = templates[currentLang];
            cachedCode[currentLang] = templates[currentLang];
        }
    });

    // Clear console handler
    clearBtn.addEventListener("click", () => {
        consoleDiv.innerHTML = '<span style="color: var(--text-muted);">Console cleared.</span>';
    });

    // Run Code handler
    runBtn.addEventListener("click", async () => {
        const code = editor.value;
        consoleDiv.textContent = "";
        runBtn.disabled = true;
        
        if (currentLang === "javascript") {
            statusText.textContent = "Running...";
            let output = "";
            
            const originalLog = console.log;
            const originalError = console.error;
            
            console.log = (...args) => {
                output += args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(" ") + "\n";
            };
            console.error = (...args) => {
                output += "🔴 ERROR: " + args.join(" ") + "\n";
            };
            
            try {
                // Use new Function to isolate execution context a bit
                new Function(code)();
                if (!output) {
                    output = "[Code executed successfully with no output]";
                }
                consoleDiv.textContent = output;
            } catch (err) {
                consoleDiv.innerHTML = `<span style="color: var(--accent-red);">🔴 Runtime Error: ${err.message}\n${err.stack ? err.stack.split('\n').slice(0, 3).join('\n') : ''}</span>`;
            } finally {
                console.log = originalLog;
                console.error = originalError;
                runBtn.disabled = false;
                statusText.textContent = "Ready";
            }
        } 
        else if (currentLang === "python") {
            try {
                if (!pyodideInstance) {
                    if (isPyodideLoading) return;
                    isPyodideLoading = true;
                    statusText.textContent = "Initializing Pyodide WASM runtime (approx 5-10s)...";
                    consoleDiv.textContent = "Loading WebAssembly Python environment...\n";
                    pyodideInstance = await loadPyodide();
                    isPyodideLoading = false;
                    statusText.textContent = "Pyodide Loaded";
                    consoleDiv.textContent += "Pyodide Environment Ready!\n\n";
                }
                
                statusText.textContent = "Running Python...";
                let pyOutput = "";
                
                // Set stdout and stderr redirects
                pyodideInstance.setStdout({
                    write: (text) => {
                        pyOutput += text;
                        return text.length;
                    }
                });
                
                pyodideInstance.setStderr({
                    write: (text) => {
                        pyOutput += text;
                        return text.length;
                    }
                });
                
                // Run python asynchronously
                await pyodideInstance.runPythonAsync(code);
                
                if (!pyOutput) {
                    pyOutput = "[Python code executed successfully with no output]";
                }
                consoleDiv.textContent = pyOutput;
                
            } catch (err) {
                consoleDiv.innerHTML = `<span style="color: var(--accent-red);">🔴 Python Execution Error:\n${escapeHtml(err.message)}</span>`;
            } finally {
                runBtn.disabled = false;
                statusText.textContent = "Ready";
            }
        }
    });
});

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
