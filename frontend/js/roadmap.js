document.addEventListener("DOMContentLoaded", async () => {
    hydrateUserBadge();
    await loadRoadmaps();
});

function hydrateUserBadge() {
    const user = getUser();
    if (!user) return;
    document.getElementById("user-name").textContent = user.name;
    const badge = document.getElementById("user-exp-badge");
    badge.textContent = user.profile.experience_level;
    badge.className = `experience-tag exp-${user.profile.experience_level}`;
}

async function loadRoadmaps() {
    const list = document.getElementById("roadmap-list");
    const toc = document.getElementById("roadmap-toc-list");
    try {
        const domainsRes = await authFetch("/domains");
        const domains = await domainsRes.json();
        const domainTopicPairs = await Promise.all(domains.map(async domain => {
            const topicsRes = await authFetch(`/domains/${domain.slug}/topics`);
            return { domain, topics: topicsRes.ok ? await topicsRes.json() : [] };
        }));
        renderRoadmaps(domainTopicPairs);
        renderToc(domainTopicPairs);
        setupScrollSpy();
    } catch (err) {
        console.error(err);
        list.innerHTML = `<div class="glass-panel empty-state">Could not load roadmaps.</div>`;
        toc.textContent = "Unavailable";
    }
}

function renderToc(items) {
    document.getElementById("roadmap-toc-list").innerHTML = items.map(({ domain }) =>
        `<a class="roadmap-toc-link" href="#domain-${domain.slug}">${escapeHtml(domain.title)}</a>`
    ).join("");
}

function renderRoadmaps(items) {
    document.getElementById("roadmap-list").innerHTML = items.map(({ domain, topics }) => `
        <article class="roadmap-domain glass-panel" id="domain-${domain.slug}">
            <div class="roadmap-domain-header">
                <div>
                    <span class="roadmap-eyebrow">${topics.length} topics</span>
                    <h2>${escapeHtml(domain.title)}</h2>
                </div>
                <p>${escapeHtml(domain.description)}</p>
            </div>
            <div class="roadmap-topic-stack">
                ${topics.map((topic, index) => renderTopic(topic, index)).join("") || `<p class="muted-text">No topics yet.</p>`}
            </div>
        </article>
    `).join("");
}

function renderTopic(topic, index) {
    const resources = [];
    (topic.subtopics || []).forEach(subtopic => (subtopic.content_blocks || []).forEach(block => {
        if (block.type === "resource_link") resources.push(block);
    }));

    return `
        <section class="roadmap-topic">
            <a class="roadmap-topic-title" href="/topic/${topic.slug}">
                <span>${String(index + 1).padStart(2, "0")}</span>
                <strong>${escapeHtml(topic.title)}</strong>
                <em>${escapeHtml(topic.difficulty)}</em>
            </a>
            <div class="roadmap-subtopics">
                ${(topic.subtopics || []).map(sub => `<a href="/topic/${topic.slug}" class="roadmap-subtopic">${escapeHtml(sub.title)}</a>`).join("")}
            </div>
            <div class="roadmap-resources">
                ${resources.slice(0, 3).map(link => `<a href="${link.url}" target="_blank" rel="noopener">${escapeHtml(link.label || "Resource")}</a>`).join("")}
            </div>
        </section>
    `;
}

function setupScrollSpy() {
    const links = [...document.querySelectorAll(".roadmap-toc-link")];
    const sections = links.map(link => document.querySelector(link.getAttribute("href"))).filter(Boolean);
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            links.forEach(link => link.classList.toggle("active", link.getAttribute("href") === `#${entry.target.id}`));
        });
    }, { rootMargin: "-25% 0px -65% 0px" });
    sections.forEach(section => observer.observe(section));
}

function escapeHtml(text) {
    return String(text || "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}
