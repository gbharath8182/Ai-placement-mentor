let currentTopicSlug = "";
let currentProblemId = "";
let starterCodeCache = "";
let lessonChecks = [];
let currentTopic = null;

document.addEventListener("DOMContentLoaded", async () => {
    currentTopicSlug = decodeURIComponent(window.location.pathname.split("/").pop());
    const user = getUser();
    if (user) {
        document.getElementById("user-name").textContent = user.name;
        const badge = document.getElementById("user-exp-badge");
        badge.textContent = user.profile?.experience_level || "fresher";
    }
    if (!getAccessToken()) {
        document.querySelectorAll(".ai-actions-bar button, #chat-send-btn, #chat-input").forEach(element => { element.disabled = true; });
        const logs = document.getElementById("ai-chat-logs");
        const note = document.createElement("p");
        note.textContent = "Sign in to ask your tutor questions, save assessments and track mastery.";
        const link = document.createElement("a");
        link.href = "/login";
        link.textContent = "Sign in";
        logs.replaceChildren(note, link);
    }
    await loadTopicData();
    if (getAccessToken()) await Promise.allSettled([loadPracticeProblem(), restoreTutorHistory()]);
    document.getElementById("reset-code-btn")?.addEventListener("click", () => {
        if (confirm("Reset the editor to starter code?")) document.getElementById("editor").value = starterCodeCache;
    });
    document.getElementById("run-code-btn")?.addEventListener("click", runCodeSubmission);
});

async function loadTopicData() {
    const area = document.getElementById("content-blocks-area");
    try {
        const response = await fetch(`/topics/${encodeURIComponent(currentTopicSlug)}`);
        if (!response.ok) throw new Error(response.status === 404 ? "This lesson could not be found." : "Lesson content is temporarily unavailable.");
        currentTopic = await response.json();
        document.title = `${currentTopic.title} | AI Placement Mentor`;
        document.getElementById("topic-title").textContent = currentTopic.title;
        document.getElementById("topic-difficulty-badge").textContent = currentTopic.difficulty;
        if (getAccessToken()) {
            const response = await authFetch(`/learning/${encodeURIComponent(currentTopicSlug)}/checks`);
            if (response.ok) {
                const payload = await response.json();
                lessonChecks = Array.isArray(payload) ? payload : payload.checks || [];
            }
        }
        renderLessonOverview(currentTopic);
        const sidebar = document.getElementById("subtopics-list-container");
        sidebar.replaceChildren();
        const sections = currentTopic.subtopics?.length ? currentTopic.subtopics : [{ title: "Lesson", content_blocks: currentTopic.content_blocks || [] }];
        sections.forEach((section, index) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "lesson-section-link topic-item";
            button.textContent = `${index + 1}. ${section.title}`;
            button.addEventListener("click", () => {
                sidebar.querySelectorAll("button").forEach(item => { item.classList.remove("active"); item.removeAttribute("aria-current"); });
                button.classList.add("active");
                button.setAttribute("aria-current", "true");
                document.getElementById("subtopic-title-badge").textContent = section.title;
                renderContentBlocks(section.content_blocks, currentTopic.subtopics?.length ? index : null);
            });
            sidebar.appendChild(button);
        });
        sidebar.firstChild?.click();
        await Promise.allSettled([loadLessonNavigation(currentTopic), refreshMastery(), updateTopicProgress("in_progress")]);
    } catch (error) {
        document.getElementById("topic-title").textContent = "Lesson unavailable";
        const message = document.createElement("p");
        message.textContent = error.message;
        const retry = document.createElement("button");
        retry.type = "button";
        retry.className = "btn-secondary";
        retry.textContent = "Retry loading lesson";
        retry.addEventListener("click", loadTopicData);
        area.replaceChildren(message, retry);
    }
}

function renderLessonOverview(topic) {
    const overview = document.getElementById("lesson-overview");
    if (!overview) return;
    overview.replaceChildren();
    if (topic.objectives?.length) {
        const heading = document.createElement("h2");
        heading.textContent = "What you’ll learn";
        const list = document.createElement("ul");
        topic.objectives.forEach(objective => { const item = document.createElement("li"); item.textContent = objective; list.appendChild(item); });
        overview.append(heading, list);
    }
    if (topic.prerequisites?.length) {
        const label = document.createElement("p");
        label.textContent = "Before you start: ";
        topic.prerequisites.forEach((slug, index) => {
            const link = document.createElement("a");
            link.href = `/topic/${encodeURIComponent(slug)}`;
            link.textContent = slug.replace(/^python-foundations-/, "").replace(/-/g, " ");
            if (index) label.append(", ");
            label.appendChild(link);
        });
        overview.appendChild(label);
    }
}

async function loadLessonNavigation(topic) {
    const navigation = document.getElementById("lesson-navigation");
    if (!navigation) return;
    const response = await fetch(`/domains/${encodeURIComponent(topic.domain_slug)}/topics`);
    if (!response.ok) return;
    const lessons = await response.json();
    lessons.sort((first, second) => (first.order ?? 999) - (second.order ?? 999));
    const index = lessons.findIndex(lesson => lesson.slug === currentTopicSlug);
    navigation.replaceChildren();
    [[lessons[index - 1], "← Previous lesson"], [lessons[index + 1], "Next lesson →"]].forEach(([lesson, label]) => {
        if (!lesson) return;
        const link = document.createElement("a");
        link.className = "btn-secondary";
        link.href = `/topic/${encodeURIComponent(lesson.slug)}`;
        link.textContent = `${label}: ${lesson.title}`;
        navigation.appendChild(link);
    });
}

function safeResourceURL(value) {
    try { const parsed = new URL(value); return ["https:", "http:"].includes(parsed.protocol) ? parsed.href : null; }
    catch { return null; }
}

function renderContentBlocks(blocks, subtopicIndex = null) {
    const area = document.getElementById("content-blocks-area");
    area.replaceChildren();
    if (!blocks?.length) { area.textContent = "This lesson is being prepared. Choose another section or explore the curriculum."; return; }
    blocks.forEach((block, blockIndex) => {
        const element = document.createElement("section");
        element.className = `block-${String(block.type).replace(/[^a-z_]/g, "")}`;
        if (block.type === "heading") {
            const heading = document.createElement(`h${[2, 3, 4].includes(block.level) ? block.level : 2}`);
            heading.textContent = block.value;
            element.appendChild(heading);
        } else if (block.type === "code") {
            const label = document.createElement("span");
            label.className = "code-lang-label";
            label.textContent = block.language || "code";
            const pre = document.createElement("pre");
            const code = document.createElement("code");
            code.textContent = block.value;
            pre.appendChild(code);
            element.append(label, pre);
            if (block.expected_output != null) {
                const expected = document.createElement("pre");
                expected.className = "example-output";
                expected.textContent = `Expected output\n${block.expected_output}`;
                element.appendChild(expected);
            }
        } else if (block.type === "list") {
            const list = document.createElement(block.ordered ? "ol" : "ul");
            (block.items || []).forEach(value => { const item = document.createElement("li"); item.innerHTML = formatLessonText(String(value)); list.appendChild(item); });
            element.appendChild(list);
        } else if (block.type === "callout") {
            element.classList.add("lesson-callout");
            const label = document.createElement("strong");
            label.textContent = block.title || block.kind || "Note";
            const paragraph = document.createElement("p");
            paragraph.innerHTML = formatLessonText(block.value || "");
            element.append(label, paragraph);
        } else if (block.type === "diagram") {
            const label = document.createElement("h3");
            label.textContent = block.title || "Execution trace";
            const diagram = document.createElement("pre");
            diagram.className = "mermaid";
            diagram.textContent = block.value;
            element.append(label, diagram);
        } else if (block.type === "knowledge_check") {
            renderKnowledgeCheck(block, element, subtopicIndex, blockIndex);
        } else if (block.type === "resource_link") {
            const url = safeResourceURL(block.url);
            if (!url) return;
            const link = document.createElement("a");
            link.className = "block-resource";
            link.href = url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = block.label || url;
            element.appendChild(link);
        } else if (block.type === "divider") {
            element.appendChild(document.createElement("hr"));
        } else {
            const paragraph = document.createElement("p");
            paragraph.innerHTML = formatLessonText(block.value || "");
            element.appendChild(paragraph);
        }
        area.appendChild(element);
    });
    if (window.mermaid) {
        mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: document.documentElement.classList.contains("light-theme") ? "default" : "dark" });
        mermaid.run({ nodes: area.querySelectorAll(".mermaid") }).catch(() => {});
    }
    window.MathJax?.typesetPromise?.([area]).catch(() => {});
}

function resolveLessonCheck(block, subtopicIndex, blockIndex) {
    const identity = block.block_id || block.id;
    if (identity) return lessonChecks.find(item => (item.block_id || item.id) === identity);
    return lessonChecks.find(item => item.subtopic_index === subtopicIndex && item.block_index === blockIndex);
}

function renderKnowledgeCheck(block, element, subtopicIndex, blockIndex) {
    element.className = "knowledge-check";
    const question = document.createElement("h3");
    question.textContent = block.question;
    const feedback = document.createElement("p");
    feedback.className = "knowledge-result";
    feedback.setAttribute("aria-live", "polite");
    const options = document.createElement("div");
    options.className = "knowledge-options";
    const check = resolveLessonCheck(block, subtopicIndex, blockIndex);
    (block.options || []).forEach((option, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "knowledge-option";
        button.textContent = option;
        button.addEventListener("click", async () => {
            if (!getAccessToken()) { feedback.textContent = "Sign in to answer and save your assessment."; return; }
            if (!check) { feedback.textContent = "This assessment is temporarily unavailable. Reload the lesson to retry."; return; }
            options.querySelectorAll("button").forEach(item => { item.disabled = true; });
            feedback.textContent = "Checking your answer…";
            try {
                const response = await authFetch(`/learning/${encodeURIComponent(currentTopicSlug)}/check`, { method: "POST", body: { block_id: check.block_id || check.id, selected_index: index } });
                const result = await response.json();
                if (!response.ok) throw new Error("Assessment could not be saved. Please retry.");
                button.classList.add(result.correct ? "is-correct" : "is-incorrect");
                feedback.textContent = `${result.correct ? "Correct" : "Review this concept"}. ${result.explanation || ""}`;
                await refreshMastery();
                trackActivity("quiz", 1, currentTopicSlug);
            } catch (error) { feedback.textContent = error.message; }
            finally { options.querySelectorAll("button").forEach(item => { item.disabled = false; }); }
        });
        options.appendChild(button);
    });
    element.append(question, options, feedback);
}

async function refreshMastery() {
    const panel = document.getElementById("mastery-panel");
    if (!panel) return;
    if (!getAccessToken()) { panel.textContent = "Sign in to save assessments and see evidence of your understanding."; return; }
    const response = await authFetch(`/learning/${encodeURIComponent(currentTopicSlug)}/mastery`);
    if (!response.ok) { panel.textContent = "Your mastery evidence is temporarily unavailable. Your lesson is still readable."; return; }
    const mastery = await response.json();
    panel.replaceChildren();
    const heading = document.createElement("h2");
    heading.textContent = `Learning evidence · ${(mastery.status || "not_assessed").replace(/_/g, " ")}`;
    const description = document.createElement("p");
    description.textContent = mastery.reason || (mastery.reasons || []).join(" ") || "Answer lesson checks and solve coding exercises to assess your understanding.";
    panel.append(heading, description);
    if (mastery.score != null) { const score = document.createElement("p"); score.textContent = `Evidence score: ${Math.round(mastery.score)}%. Reading time does not count as mastery.`; panel.appendChild(score); }
    (mastery.missed_questions || []).forEach(item => { const missed = document.createElement("p"); missed.textContent = `Review: ${item.question || item.source_id || item}`; panel.appendChild(missed); });
}

async function loadPracticeProblem() {
    try {
        const response = await authFetch(`/practice/${encodeURIComponent(currentTopicSlug)}`);
        if (!response.ok) return;
        const problems = await response.json();
        if (!problems.length) return;
        const problem = problems[0];
        currentProblemId = problem.id;
        starterCodeCache = problem.starter_code;
        document.getElementById("problem-title").textContent = problem.title;
        document.getElementById("problem-desc").textContent = problem.description;
        document.getElementById("editor").value = starterCodeCache;
        document.getElementById("problem-difficulty-badge").textContent = problem.difficulty;
        document.getElementById("practice-playground").style.display = "block";
    } catch { }
}

async function runCodeSubmission() {
    const button = document.getElementById("run-code-btn");
    const container = document.getElementById("test-case-container");
    button.disabled = true;
    button.textContent = "Running…";
    container.textContent = "Checking stored test cases in the remote sandbox…";
    try {
        const response = await authFetch(`/practice/${currentProblemId}/submit`, { method: "POST", body: { language: document.getElementById("lang-select").value, code: document.getElementById("editor").value } });
        const payload = await response.json();
        if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Execution is unavailable. Please retry.");
        document.getElementById("compiler-status-title").textContent = payload.overall_passed ? "All test cases passed" : "Review failed cases";
        container.replaceChildren();
        payload.results.forEach((result, index) => {
            const item = document.createElement("div");
            item.className = "test-case-item";
            const heading = document.createElement("strong");
            heading.textContent = `Case ${index + 1}: ${result.passed ? "Passed" : "Failed"}`;
            const details = document.createElement("pre");
            details.textContent = `Input: ${result.input}\nExpected: ${result.expected}\nActual: ${result.actual || "[no output]"}${result.stderr ? `\nError: ${result.stderr}` : ""}`;
            item.append(heading, details);
            container.appendChild(item);
        });
        await refreshMastery();
        trackActivity("practice", 1, currentTopicSlug);
    } catch (error) { container.textContent = error.message; }
    finally { button.disabled = false; button.textContent = "Run Solution"; }
}

async function updateTopicProgress(status) {
    if (!getAccessToken()) return;
    await authFetch("/progress/update", { method: "POST", body: { topic_slug: currentTopicSlug, status } });
}

function formatLessonText(text) {
    return escapeHtml(text).replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/`([^`\n]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>");
}

function escapeHtml(text) {
    return String(text || "").replace(/[&<>"']/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[character]));
}
