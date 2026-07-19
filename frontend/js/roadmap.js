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
                <button class="btn-secondary roadmap-detail-toggle" data-slug="${domain.slug}">View Full Roadmap &darr;</button>
            </div>
            <div class="roadmap-topic-stack">
                ${topics.map((topic, index) => renderTopic(topic, index)).join("") || `<p class="muted-text">No topics yet.</p>`}
            </div>
            <div class="roadmap-detail-panel" id="detail-${domain.slug}" style="display:none;"></div>
        </article>
    `).join("");

    document.querySelectorAll(".roadmap-detail-toggle").forEach(btn => {
        btn.addEventListener("click", () => toggleDomainDetail(btn.dataset.slug, btn));
    });
}

async function toggleDomainDetail(slug, btn) {
    const panel = document.getElementById(`detail-${slug}`);
    const isOpen = panel.style.display === "block";

    if (isOpen) {
        panel.style.display = "none";
        btn.textContent = "View Full Roadmap \u2193";
        return;
    }

    if (!panel.dataset.loaded) {
        panel.innerHTML = `<p class="muted-text">Loading detailed roadmap...</p>`;
        panel.style.display = "block";
        try {
            const res = await authFetch(`/domains/${slug}/details`);
            if (res.ok) {
                const detail = await res.json();
                panel.innerHTML = renderDomainDetail(detail);
                panel.dataset.loaded = "true";
            } else {
                panel.innerHTML = `<p class="muted-text">A detailed roadmap for this domain hasn't been published yet. Check back soon!</p>`;
            }
        } catch (err) {
            console.error(err);
            panel.innerHTML = `<p class="muted-text">Could not load detailed roadmap.</p>`;
        }
    } else {
        panel.style.display = "block";
    }

    btn.textContent = "Hide Full Roadmap \u2191";
}

function renderDomainDetail(d) {
    const chips = (arr) => (arr || []).map(item => `<span class="detail-chip">${escapeHtml(item)}</span>`).join("");

    const roadmapTiers = (d.roadmap || []).map(tier => `
        <div class="detail-tier">
            <h4 class="detail-tier-label">${escapeHtml(tier.tier)}</h4>
            <ul>${(tier.items || []).map(i => `<li>${escapeHtml(i)}</li>`).join("")}</ul>
        </div>
    `).join("");

    const topics = (d.topics || []).map(t => `
        <div class="detail-topic-card glass-panel">
            <div class="detail-topic-head">
                <strong>${escapeHtml(t.name)}</strong>
                <em>${escapeHtml(t.difficulty)} &middot; ${escapeHtml(t.estimated_time)}</em>
            </div>
            <p>${escapeHtml(t.description)}</p>
            <p class="detail-importance"><strong>Why it matters:</strong> ${escapeHtml(t.importance)}</p>
            ${t.prerequisites && t.prerequisites.length ? `<p><strong>Prerequisites:</strong> ${chips(t.prerequisites)}</p>` : ""}
            ${t.resources ? `
                <div class="detail-resources">
                    ${t.resources.documentation ? `<a href="${t.resources.documentation}" target="_blank">Documentation</a>` : ""}
                    ${t.resources.youtube_playlist ? `<a href="${t.resources.youtube_playlist}" target="_blank">Video Playlist</a>` : ""}
                    ${(t.resources.articles || []).map(a => `<a href="${a}" target="_blank">Article</a>`).join("")}
                </div>
                ${t.resources.cheat_sheet ? `<p class="detail-cheatsheet"><strong>Cheat sheet:</strong> ${escapeHtml(t.resources.cheat_sheet)}</p>` : ""}
            ` : ""}
            ${t.practice_questions && t.practice_questions.length ? `<div><strong>Practice:</strong> ${chips(t.practice_questions)}</div>` : ""}
            ${t.interview_questions && t.interview_questions.length ? `<div><strong>Interview questions:</strong><ul>${t.interview_questions.map(q => `<li>${escapeHtml(q)}</li>`).join("")}</ul></div>` : ""}
        </div>
    `).join("");

    const projects = (d.projects || []).map(p => `
        <div class="detail-project-card glass-panel">
            <span class="detail-project-tier">${escapeHtml(p.tier)}</span>
            <strong>${escapeHtml(p.title)}</strong>
            <p>${escapeHtml(p.description)}</p>
            <div>${chips(p.technologies_used)}</div>
        </div>
    `).join("");

    const companyPrep = (d.company_prep || []).map(c => `
        <div class="detail-company-card glass-panel">
            <strong>${escapeHtml(c.group_name)}</strong>
            <p>${(c.example_companies || []).join(", ")}</p>
            <div>${chips(c.focus_areas)}</div>
        </div>
    `).join("");

    return `
        <div class="domain-detail-inner">
            <section class="detail-section">
                <h3>Overview</h3>
                <p>${escapeHtml(d.overview)}</p>
                <p><strong>Why it matters:</strong> ${escapeHtml(d.why_important)}</p>
                <p><strong>Future scope:</strong> ${escapeHtml(d.future_scope)}</p>
                ${d.average_salary ? `<p><strong>Average salary:</strong> ${escapeHtml(d.average_salary)}</p>` : ""}
                <p><strong>Industries:</strong> ${chips(d.industries_using)}</p>
                <p><strong>Skills required:</strong> ${chips(d.skills_required)}</p>
            </section>

            <section class="detail-section">
                <h3>Prerequisites</h3>
                <p>${chips(d.prerequisites)}</p>
            </section>

            <section class="detail-section">
                <h3>Learning Roadmap</h3>
                <div class="detail-tier-grid">${roadmapTiers}</div>
            </section>

            <section class="detail-section">
                <h3>Topics In Depth</h3>
                <div class="detail-topic-grid">${topics}</div>
            </section>

            <section class="detail-section">
                <h3>Practice Platforms</h3>
                <p>${chips(d.practice_platforms)}</p>
            </section>

            <section class="detail-section">
                <h3>Projects</h3>
                <div class="detail-project-grid">${projects}</div>
            </section>

            <section class="detail-section">
                <h3>Interview Preparation</h3>
                <p><strong>Important topics:</strong> ${chips(d.interview_prep ? d.interview_prep.important_topics : [])}</p>
                <p><strong>Coding questions:</strong> ${chips(d.interview_prep ? d.interview_prep.coding_questions : [])}</p>
                <p><strong>System design questions:</strong> ${chips(d.interview_prep ? d.interview_prep.system_design_questions : [])}</p>
                <p><strong>HR questions:</strong> ${chips(d.interview_prep ? d.interview_prep.hr_questions : [])}</p>
            <button class="btn-primary mi-start-btn" onclick=\"openMockInterviewModal('${d.domain_slug}')\">Start Mock Interview</button>
            </section>

            <section class="detail-section">
                <h3>Resume Tips</h3>
                <ul>${(d.resume_tips || []).map(tip => `<li>${escapeHtml(tip)}</li>`).join("")}</ul>
            </section>

            <section class="detail-section">
                <h3>Certifications</h3>
                <ul>${(d.certifications || []).map(c => `<li>${escapeHtml(c)}</li>`).join("")}</ul>
            </section>

            <section class="detail-section">
                <h3>Company Preparation</h3>
                <div class="detail-company-grid">${companyPrep}</div>
            </section>
        </div>
    `;
}

function renderTopic(topic, index) {
    const resources = [];
    (topic.subtopics || []).forEach(subtopic => (subtopic.content_blocks || []).forEach(block => {
        if (block.type === "resource_link" && !resources.some(r => r.url === block.url)) resources.push(block);
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

