let aiBusy = false;
let activeAIRequest = null;

async function restoreTutorHistory() {
    if (!getAccessToken() || !currentTopicSlug) return;
    setAIBusy(true);
    try {
        const response = await authFetch(`/ai/history/${encodeURIComponent(currentTopicSlug)}`);
        if (!response.ok) throw new Error("history_unavailable");
        const payload = await response.json();
        const messages = (Array.isArray(payload.messages) ? payload.messages : []).filter(message =>
            ["user", "assistant"].includes(message.role) && typeof message.content === "string"
        ).slice(-20);
        if (messages.length) {
            document.getElementById("ai-chat-logs").replaceChildren();
            messages.forEach(message => {
                if (message.role === "user") appendUserBubble(message.content);
                else window.appendAssistantMessage(message.content);
            });
        }
    } catch {
        const notice = document.createElement("p");
        notice.className = "ai-error";
        notice.textContent = "Saved conversation could not be loaded. You can still ask a new question.";
        document.getElementById("ai-chat-logs").appendChild(notice);
    } finally {
        setAIBusy(false);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ai-chat-form");
    if (!form) return;
    form.addEventListener("submit", async event => {
        event.preventDefault();
        const input = document.getElementById("chat-input");
        const message = input.value.trim();
        if (!message || aiBusy) return;
        input.value = "";
        await sendUserMessage(message);
    });
    document.getElementById("chip-explain-simply")?.addEventListener("click", () => runExplainEndpoint("fresher", "Explain Simply"));
    document.getElementById("chip-deep-dive")?.addEventListener("click", () => runExplainEndpoint("experienced", "Deeper Dive"));
    document.getElementById("chip-quiz")?.addEventListener("click", () => sendUserMessage("Quiz me on the selected lesson section. Ask one question and wait for my answer."));
    const stop = document.createElement("button");
    stop.type = "button";
    stop.className = "btn-chip";
    stop.id = "ai-stop-btn";
    stop.textContent = "Stop reply";
    stop.hidden = true;
    stop.addEventListener("click", () => activeAIRequest?.abort());
    form.parentElement.appendChild(stop);
    window.addEventListener("pagehide", () => activeAIRequest?.abort());
});

function setAIBusy(busy) {
    aiBusy = busy;
    document.querySelectorAll(".ai-actions-bar button, #chat-send-btn").forEach(button => { button.disabled = busy; });
    const status = document.getElementById("ai-status-text");
    if (status) status.textContent = busy ? "Thinking…" : "Lesson companion";
    const stop = document.getElementById("ai-stop-btn");
    if (stop) stop.hidden = !busy;
}

function appendUserBubble(text) {
    const logs = document.getElementById("ai-chat-logs");
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble bubble-user";
    bubble.textContent = text;
    logs.appendChild(bubble);
    logs.scrollTop = logs.scrollHeight;
}

function formatTutorText(text) {
    let escaped = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    escaped = escaped.replace(/```[\w+-]*\n([\s\S]*?)```/g, (_, code) => `<pre><code>${code.trim()}</code></pre>`);
    return escaped.replace(/`([^`\n]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");
}

function createAssistantPlaceholder() {
    const logs = document.getElementById("ai-chat-logs");
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble bubble-assistant";
    bubble.textContent = "Thinking…";
    bubble.setAttribute("aria-busy", "true");
    logs.appendChild(bubble);
    let content = "";
    return {
        update(text) {
            content += text;
            bubble.innerHTML = formatTutorText(content);
            logs.scrollTop = logs.scrollHeight;
        },
        fail(message, retry) {
            const notice = document.createElement("p");
            notice.className = "ai-error";
            notice.textContent = message;
            if (!content) bubble.replaceChildren();
            bubble.appendChild(notice);
            if (retry) {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "btn-chip";
                button.textContent = "Retry";
                button.addEventListener("click", () => { if (!aiBusy) { button.remove(); retry(); } });
                bubble.appendChild(button);
            }
        },
        finish() {
            bubble.setAttribute("aria-busy", "false");
        }
    };
}

function safeAIError(payload) {
    const allowed = new Set(["authentication", "model_unavailable", "rate_limit", "service", "timeout", "network", "invalid_request", "invalid_response", "not_configured", "database"]);
    const error = payload?.error;
    if (error && allowed.has(error.code) && typeof error.message === "string") return error;
    return { message: "The assistant is temporarily unavailable. Please retry shortly.", retryable: true };
}

async function sendUserMessage(messageText) {
    if (aiBusy) return;
    appendUserBubble(messageText);
    const placeholder = createAssistantPlaceholder();
    activeAIRequest = new AbortController();
    setAIBusy(true);
    let reader;
    let completed = false;
    let failed = false;
    try {
        const response = await authFetch("/ai/chat", {
            method: "POST", signal: activeAIRequest.signal,
            body: { topic_slug: currentTopicSlug, message: messageText, subtopic_title: document.getElementById("subtopic-title-badge")?.textContent || null }
        });
        if (!response.ok) {
            const error = safeAIError(await response.json().catch(() => ({})));
            placeholder.fail(error.message, error.retryable ? () => sendUserMessage(messageText) : null);
            return;
        }
        reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (true) {
            const { value, done } = await reader.read();
            buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = done ? "" : lines.pop();
            for (const line of lines) {
                if (!line.startsWith("data:")) continue;
                const data = line.slice(5).trim();
                if (data === "[DONE]") { completed = true; continue; }
                const event = JSON.parse(data);
                if (event.error) {
                    const error = safeAIError(event);
                    placeholder.fail(error.message, error.retryable ? () => sendUserMessage(messageText) : null);
                    failed = true;
                } else {
                    placeholder.update(event.choices?.[0]?.delta?.content || "");
                }
            }
            if (done || completed || failed) break;
        }
        if (!completed && !failed) placeholder.fail("The reply was interrupted. Please retry.", () => sendUserMessage(messageText));
    } catch (error) {
        placeholder.fail(error.name === "AbortError" ? "Reply stopped." : "The connection was interrupted. Please retry.", () => sendUserMessage(messageText));
    } finally {
        if (reader) { await reader.cancel().catch(() => {}); reader.releaseLock(); }
        placeholder.finish();
        setAIBusy(false);
        activeAIRequest = null;
    }
}

async function runExplainEndpoint(level, actionName) {
    if (aiBusy) return;
    appendUserBubble(`${actionName} requested.`);
    const placeholder = createAssistantPlaceholder();
    activeAIRequest = new AbortController();
    setAIBusy(true);
    try {
        const response = await authFetch("/ai/explain", { method: "POST", signal: activeAIRequest.signal, body: { topic_slug: currentTopicSlug, level } });
        const data = await response.json();
        if (response.ok) placeholder.update(data.explanation);
        else {
            const error = safeAIError(data);
            placeholder.fail(error.message, error.retryable ? () => runExplainEndpoint(level, actionName) : null);
        }
    } catch (error) {
        placeholder.fail(error.name === "AbortError" ? "Reply stopped." : "The connection was interrupted. Please retry.", () => runExplainEndpoint(level, actionName));
    } finally {
        placeholder.finish();
        setAIBusy(false);
        activeAIRequest = null;
    }
}

window.appendAssistantMessage = message => {
    const placeholder = createAssistantPlaceholder();
    placeholder.update(message);
    placeholder.finish();
};
