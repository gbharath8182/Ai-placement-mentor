const resumeForm = document.getElementById("resume-form");
const projects = document.getElementById("projects");
let generatedResume = null;

function resumeElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
}

function safeResumeLink(value) {
    if (!value || /[\u0000-\u001f\\]/.test(value)) return "";
    if (/^mailto:[A-Za-z0-9.!#$%&'*+/=^_`{|}~-]+@[A-Za-z0-9.-]+$/.test(value)) return value;
    try {
        const url = new URL(value);
        return ["https:", "http:"].includes(url.protocol) && !url.username && !url.password ? url.href : "";
    } catch { return ""; }
}

function appendResumeSpans(element, spans) {
    spans.forEach(span => {
        const href = safeResumeLink(span.href);
        const text = resumeElement(span.bold ? "strong" : "span", "", span.text);
        if (!href) { element.appendChild(text); return; }
        const link = resumeElement("a");
        link.href = href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.appendChild(text);
        element.appendChild(link);
    });
}

function renderResume(documentData) {
    if (!documentData || !Array.isArray(documentData.blocks) || !Array.isArray(documentData.contacts)) {
        throw new Error("The resume could not be formatted. Please try generating it again.");
    }
    const output = document.getElementById("resume-output");
    const header = resumeElement("header", "resume-paper-header");
    header.appendChild(resumeElement("h1", "", documentData.full_name));
    if (documentData.target_role) header.appendChild(resumeElement("p", "resume-paper-role", documentData.target_role));
    const contacts = resumeElement("div", "resume-paper-contacts");
    documentData.contacts.forEach(contact => {
        const item = resumeElement("span");
        appendResumeSpans(item, [contact]);
        contacts.appendChild(item);
    });
    header.appendChild(contacts);
    output.replaceChildren(header);
    let list = null;
    documentData.blocks.forEach(block => {
        if (!["heading", "subheading", "paragraph", "bullet"].includes(block.kind)) return;
        if (block.kind === "bullet") {
            if (!list) { list = resumeElement("ul"); output.appendChild(list); }
            const item = resumeElement("li");
            appendResumeSpans(item, block.spans);
            list.appendChild(item);
            return;
        }
        list = null;
        const element = resumeElement({ heading: "h2", subheading: "h3", paragraph: "p" }[block.kind]);
        appendResumeSpans(element, block.spans);
        output.appendChild(element);
    });
    output.classList.remove("hidden");
    document.getElementById("resume-empty")?.classList.add("hidden");
}

function resumeError(result, fallback) {
    if (typeof result.detail === "string") return result.detail;
    if (Array.isArray(result.detail)) return result.detail.map(item => `${item.loc?.at(-1) || "Field"}: ${item.msg}`).join(". ");
    return fallback;
}

async function downloadResume() {
    if (!generatedResume) return;
    const documentData = generatedResume;
    const download = document.getElementById("download-resume");
    const status = document.getElementById("resume-status");
    download.disabled = true;
    download.textContent = "Preparing PDF…";
    try {
        const response = await authFetch("/resume/export", { method: "POST", body: documentData });
        if (!response.ok) throw new Error(resumeError(await response.json(), "PDF export failed. Please try again."));
        if (!response.headers.get("content-type")?.includes("application/pdf")) throw new Error("The server did not return a PDF. Please try again.");
        const blob = await response.blob();
        const href = URL.createObjectURL(blob);
        const link = resumeElement("a");
        link.href = href;
        const name = documentData.full_name.replace(/[^\p{L}\p{N} -]/gu, "").trim().replace(/\s+/g, "-").slice(0, 80);
        link.download = `${name || "Resume"}-Resume.pdf`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(href), 1000);
        if (generatedResume === documentData) status.textContent = "PDF downloaded. Review your details and links before sending it.";
    } catch (error) {
        if (generatedResume === documentData) status.textContent = error.message;
    } finally {
        download.disabled = false;
        download.textContent = "Download PDF";
    }
}

function splitLines(value) {
    return value.split(/\n|,/).map(item => item.trim()).filter(Boolean);
}

function addProject() {
    const project = document.getElementById("project-template").content.cloneNode(true);
    project.querySelector(".resume-remove").addEventListener("click", (event) => event.target.closest(".resume-project").remove());
    projects.appendChild(project);
}

function projectPayload() {
    return [...projects.querySelectorAll(".resume-project")].map(card => ({
        title: card.querySelector('[data-project="title"]').value.trim(),
        description: card.querySelector('[data-project="description"]').value.trim(),
        technologies: splitLines(card.querySelector('[data-project="technologies"]').value),
        github_url: card.querySelector('[data-project="github_url"]').value.trim(),
        live_url: card.querySelector('[data-project="live_url"]').value.trim(),
    })).filter(project => project.title || project.description);
}

document.addEventListener("DOMContentLoaded", () => {
    addProject();
    document.getElementById("add-project").addEventListener("click", addProject);
    document.getElementById("download-resume").addEventListener("click", downloadResume);
    resumeForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const data = new FormData(resumeForm);
        const payload = Object.fromEntries(data.entries());
        payload.skills = splitLines(payload.skills || "");
        payload.achievements = splitLines(payload.achievements || "");
        payload.projects = projectPayload();
        const status = document.getElementById("resume-status");
        const submit = resumeForm.querySelector("button[type=submit]");
        const download = document.getElementById("download-resume");
        submit.disabled = true;
        download.disabled = true;
        resumeForm.setAttribute("aria-busy", "true");
        status.textContent = "Preparing your resume from the details you supplied…";
        try {
            const response = await authFetch("/resume/generate", { method: "POST", body: payload });
            const result = await response.json();
            if (!response.ok) throw new Error(resumeError(result, "Could not generate your resume."));
            renderResume(result.resume_document);
            generatedResume = result.resume_document;
            status.textContent = "Ready to review. Your PDF keeps selectable text and clickable links.";
            download.classList.remove("hidden");
        } catch (error) { status.textContent = error.message; }
        finally { submit.disabled = false; download.disabled = false; resumeForm.setAttribute("aria-busy", "false"); }
    });
});
