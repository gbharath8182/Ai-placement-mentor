document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ai-chat-form");
    
    // Bind chat submission
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const input = document.getElementById("chat-input");
        const msg = input.value.trim();
        if (!msg) return;
        
        input.value = "";
        await sendUserMessage(msg);
    });
    
    // Bind action chips
    document.getElementById("chip-explain-simply").addEventListener("click", () => {
        runExplainEndpoint("fresher", "Explain Simply");
    });
    
    document.getElementById("chip-deep-dive").addEventListener("click", () => {
        runExplainEndpoint("experienced", "Deeper Dive");
    });
    
    document.getElementById("chip-quiz").addEventListener("click", () => {
        sendUserMessage("Generate a multiple-choice practice question for me on this topic.");
    });
});

// Appends a user message to the logs
function appendUserBubble(text) {
    const logs = document.getElementById("ai-chat-logs");
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble bubble-user";
    bubble.textContent = text;
    logs.appendChild(bubble);
    logs.scrollTop = logs.scrollHeight;
}

// Appends an empty assistant bubble and returns a function to add content to it
function createAssistantPlaceholder() {
    const logs = document.getElementById("ai-chat-logs");
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble bubble-assistant";
    
    // Typing indicator
    bubble.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    logs.appendChild(bubble);
    logs.scrollTop = logs.scrollHeight;
    
    let textContent = "";
    
    return {
        update: (newText) => {
            textContent += newText;
            
            // Format simple markdown-like code blocks and lists in real-time
            let formatted = textContent
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");
                
            // Format fenced code blocks: ```python ... ```
            formatted = formatted.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
                return `<pre><code>${code.trim()}</code></pre>`;
            });
            
            // Format inline code: `code`
            formatted = formatted.replace(/`(.*?)`/g, "<code>$1</code>");
            
            // Format line breaks
            formatted = formatted.replace(/\n/g, "<br>");
            
            bubble.innerHTML = formatted;
            logs.scrollTop = logs.scrollHeight;
        },
        finish: () => {
            // Remove typing indicator if empty
            if (bubble.querySelector(".typing-indicator")) {
                bubble.innerHTML = "No response could be generated.";
            }
        }
    };
}

async function sendUserMessage(messageText) {
    appendUserBubble(messageText);
    
    const placeholder = createAssistantPlaceholder();
    
    try {
        const response = await authFetch("/ai/chat", {
            method: "POST",
            body: {
                topic_slug: currentTopicSlug,
                message: messageText
            }
        });
        
        if (!response.ok) {
            placeholder.update("⚠️ Error: Failed to retrieve completions from the server.");
            placeholder.finish();
            return;
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            
            // Retain the last unfinished line in buffer
            buffer = lines.pop();
            
            for (const line of lines) {
                const cleanedLine = line.trim();
                if (cleanedLine.startsWith("data: ")) {
                    const dataStr = cleanedLine.slice(6).trim();
                    if (dataStr === "[DONE]") {
                        continue;
                    }
                    try {
                        const json = JSON.parse(dataStr);
                        if (json.error) {
                            placeholder.update(`\n⚠️ ${json.error}`);
                        } else {
                            const content = json.choices[0]?.delta?.content || "";
                            // Replace typing indicator with real text on first token
                            const indicators = document.querySelector(".typing-indicator");
                            if (indicators) {
                                // Clear typing animation
                                placeholder.update(""); 
                            }
                            placeholder.update(content);
                        }
                    } catch (e) {
                        // Not JSON or partial chunk
                    }
                }
            }
        }
        
    } catch (err) {
        console.error("AI connection error:", err);
        placeholder.update("⚠️ Connection timed out or failed. Please verify GROQ_API_KEY.");
        placeholder.finish();
    }
}

// Handler for the Explain endpoints (simplified or deep dive)
async function runExplainEndpoint(level, actionName) {
    appendUserBubble(`${actionName} requested.`);
    const placeholder = createAssistantPlaceholder();
    
    try {
        const res = await authFetch("/ai/explain", {
            method: "POST",
            body: {
                topic_slug: currentTopicSlug,
                level: level
            }
        });
        
        if (res.ok) {
            const data = await res.json();
            // Clear typing indicator and insert response
            const indicators = document.querySelector(".typing-indicator");
            if (indicators) {
                placeholder.update("");
            }
            
            // Slowly animate/stream text printing for premium feeling
            animatePrint(data.explanation, placeholder);
        } else {
            const err = await res.json();
            placeholder.update(`⚠️ Failed: ${err.detail || "Server error"}`);
            placeholder.finish();
        }
    } catch (err) {
        console.error("Error calling explain:", err);
        placeholder.update("⚠️ Error connecting to server.");
        placeholder.finish();
    }
}

function animatePrint(text, placeholder) {
    const words = text.split(" ");
    let i = 0;
    
    // Clean placeholder first
    placeholder.update("");
    
    function printNextWord() {
        if (i < words.length) {
            placeholder.update(words[i] + " ");
            i++;
            setTimeout(printNextWord, 20); // 20ms word delay
        }
    }
    
    printNextWord();
}

// Expose a helper to write standard text directly from topic completion events
window.appendAssistantMessage = (messageText) => {
    const logs = document.getElementById("ai-chat-logs");
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble bubble-assistant";
    bubble.innerHTML = messageText;
    logs.appendChild(bubble);
    logs.scrollTop = logs.scrollHeight;
};
