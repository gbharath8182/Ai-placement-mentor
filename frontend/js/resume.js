const resumeForm = document.getElementById("resume-form");
const projects = document.getElementById("projects");

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
    resumeForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const data = new FormData(resumeForm);
        const payload = Object.fromEntries(data.entries());
        payload.skills = splitLines(payload.skills || "");
        payload.achievements = splitLines(payload.achievements || "");
        payload.projects = projectPayload();
        const status = document.getElementById("resume-status");
        const output = document.getElementById("resume-output");
        const submit = resumeForm.querySelector("button[type=submit]");
        submit.disabled = true;
        status.textContent = "Creating your personalized positioning and resume…";
        output.classList.add("hidden");
        try {
            const response = await authFetch("/resume/generate", { method: "POST", body: payload });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || "Could not generate your resume.");
            const markdown = result.resume_markdown;
            output.innerHTML = window.marked ? marked.parse(markdown) : markdown.replace(/\n/g, "<br>");
            output.classList.remove("hidden");
            status.textContent = "Generated with the resume planning + writing AI pipeline.";
            const download = document.getElementById("download-resume");
            download.classList.remove("hidden");
            download.onclick = () => {
                const link = document.createElement("a");
                link.href = URL.createObjectURL(new Blob([markdown], { type: "text/markdown" }));
                link.download = `${payload.full_name.replace(/\s+/g, "-").toLowerCase() || "resume"}.md`;
                link.click(); URL.revokeObjectURL(link.href);
            };
        } catch (error) { status.textContent = error.message; }
        finally { submit.disabled = false; }
    });
});
