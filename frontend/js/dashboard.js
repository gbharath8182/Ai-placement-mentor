document.addEventListener("DOMContentLoaded", async () => {
    // 1. Populate User Details
    const user = getUser();
    if (user) {
        document.getElementById("user-name").textContent = user.name;
        document.getElementById("hero-user-name").textContent = user.name;
        
        const expBadge = document.getElementById("user-exp-badge");
        expBadge.textContent = user.profile.experience_level;
        expBadge.className = `experience-tag exp-${user.profile.experience_level}`;
    }
    
    // 2. Fetch and render Domains
    try {
        const res = await authFetch("/domains");
        if (res.ok) {
            const domains = await res.json();
            renderDomains(domains);
        } else {
            console.error("Failed to fetch domains");
        }
    } catch (err) {
        console.error("Error fetching domains:", err);
    }
    
    // 3. Fetch progress for stats widget
    try {
        if (user) {
            const progressRes = await authFetch(`/progress/${user.id}`);
            if (progressRes.ok) {
                const progressList = await progressRes.json();
                const completedCount = progressList.filter(p => p.status === 'completed').length;
                document.getElementById("stats-completed").textContent = `${completedCount} Completed`;
                if (completedCount > 0) {
                    document.getElementById("stats-streak").textContent = `${completedCount + 2} Days`;
                }
            }
        }
    } catch (err) {
        console.error("Error loading progress stats:", err);
    }
    
    // Setup close button for topics drawer
    document.getElementById("close-drawer-btn").addEventListener("click", () => {
        document.getElementById("topics-drawer").style.display = "none";
    });
});

function renderDomains(domains) {
    const grid = document.getElementById("domain-grid");
    grid.innerHTML = "";
    
    if (domains.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">No domains found. Run the seed script!</div>`;
        return;
    }
    
    domains.forEach(domain => {
        let iconHtml = ``;
        if (domain.slug === "python") {
            iconHtml = `<svg class="domain-icon-svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 8px rgba(88, 166, 255, 0.35));"><path d="M12 10H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-2"></path><path d="M12 14h6a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-6a2 2 0 0 0-2 2v2"></path><circle cx="8" cy="8" r="1" fill="currentColor"></circle><circle cx="16" cy="16" r="1" fill="currentColor"></circle></svg>`;
        } else if (domain.slug === "machine-learning") {
            iconHtml = `<svg class="domain-icon-svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--accent-secondary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 8px rgba(188, 140, 255, 0.35));"><circle cx="4" cy="6" r="2"></circle><circle cx="4" cy="12" r="2"></circle><circle cx="4" cy="18" r="2"></circle><circle cx="12" cy="6" r="2"></circle><circle cx="12" cy="12" r="2"></circle><circle cx="12" cy="18" r="2"></circle><circle cx="20" cy="9" r="2"></circle><circle cx="20" cy="15" r="2"></circle><line x1="6" y1="6" x2="10" y2="6"></line><line x1="6" y1="6" x2="10" y2="12"></line><line x1="6" y1="12" x2="10" y2="6"></line><line x1="6" y1="12" x2="10" y2="12"></line><line x1="6" y1="12" x2="10" y2="18"></line><line x1="6" y1="18" x2="10" y2="12"></line><line x1="6" y1="18" x2="10" y2="18"></line><line x1="14" y1="6" x2="18" y2="9"></line><line x1="14" y1="12" x2="18" y2="9"></line><line x1="14" y1="12" x2="18" y2="15"></line><line x1="14" y1="18" x2="18" y2="15"></line></svg>`;
        } else if (domain.slug === "dsa") {
            iconHtml = `<svg class="domain-icon-svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--accent-green)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 8px rgba(63, 185, 80, 0.35));"><circle cx="12" cy="5" r="2.5"></circle><circle cx="6" cy="12" r="2.5"></circle><circle cx="18" cy="12" r="2.5"></circle><circle cx="6" cy="19" r="2.5"></circle><line x1="10.5" y1="6.5" x2="7.5" y2="10.5"></line><line x1="13.5" y1="6.5" x2="16.5" y2="10.5"></line><line x1="6" y1="14.5" x2="6" y2="16.5"></line></svg>`;
        } else if (domain.slug === "web-dev") {
            iconHtml = `<svg class="domain-icon-svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--accent-yellow)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 8px rgba(210, 153, 34, 0.35));"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline><line x1="12" y1="2" x2="12" y2="22"></line></svg>`;
        } else if (domain.slug === "system-design") {
            iconHtml = `<svg class="domain-icon-svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--accent-secondary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 8px rgba(188, 140, 255, 0.35));"><rect x="2" y="2" width="20" height="5" rx="1"></rect><rect x="2" y="9" width="20" height="5" rx="1"></rect><rect x="2" y="16" width="20" height="5" rx="1"></rect><path d="M6 4.5h.01M6 11.5h.01M6 18.5h.01"></path></svg>`;
        } else {
            iconHtml = `<svg class="domain-icon-svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--text-main)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>`;
        }
        
        const card = document.createElement("div");
        card.className = "domain-card glass-panel";
        card.innerHTML = `
            <div class="domain-icon" style="margin-bottom: 15px;">${iconHtml}</div>
            <h3 class="domain-name">${domain.title}</h3>
            <p class="domain-desc">${domain.description}</p>
            <div class="domain-action">View Topics &rarr;</div>
        `;
        
        card.addEventListener("click", () => {
            fetchAndShowTopics(domain);
        });
        
        grid.appendChild(card);
    });
}

async function fetchAndShowTopics(domain) {
    const drawer = document.getElementById("topics-drawer");
    const listContainer = document.getElementById("topic-list");
    const drawerTitle = document.getElementById("drawer-domain-title");
    
    drawerTitle.textContent = `${domain.title} Topics`;
    listContainer.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px;">Loading topics...</div>`;
    drawer.style.display = "block";
    drawer.scrollIntoView({ behavior: "smooth" });
    
    try {
        // Fetch topics and user progress concurrently
        const user = getUser();
        const [topicsRes, progressRes] = await Promise.all([
            authFetch(`/domains/${domain.slug}/topics`),
            authFetch(`/progress/${user.id}`)
        ]);
        
        if (topicsRes.ok && progressRes.ok) {
            const topics = await topicsRes.json();
            const progressList = await progressRes.json();
            
            // Map progress by topic_slug for fast lookup
            const progressMap = {};
            progressList.forEach(p => {
                progressMap[p.topic_slug] = p.status;
            });
            
            renderTopics(topics, progressMap);
        } else {
            listContainer.innerHTML = `<div style="text-align: center; color: var(--accent-red); padding: 20px;">Failed to load topics.</div>`;
        }
    } catch (err) {
        console.error("Error loading topics:", err);
        listContainer.innerHTML = `<div style="text-align: center; color: var(--accent-red); padding: 20px;">Connection failed.</div>`;
    }
}

function renderTopics(topics, progressMap) {
    const listContainer = document.getElementById("topic-list");
    listContainer.innerHTML = "";
    
    if (topics.length === 0) {
        listContainer.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px;">No topics under this domain yet. Check back soon!</div>`;
        return;
    }
    
    topics.forEach(topic => {
        const status = progressMap[topic.slug] || "not_started";
        
        // Map status to readable label and CSS class
        let statusLabel = "Not Started";
        let statusClass = "status-not-started";
        if (status === "completed") {
            statusLabel = "Completed";
            statusClass = "status-completed";
        } else if (status === "in_progress") {
            statusLabel = "In Progress";
            statusClass = "status-in-progress";
        }
        
        const item = document.createElement("div");
        item.className = "topic-item";
        item.innerHTML = `
            <div class="topic-info">
                <span class="topic-title">${topic.title}</span>
                <div class="topic-meta">
                    <span class="problem-difficulty diff-${topic.difficulty}">${topic.difficulty}</span>
                    <span>Status: <span class="status-badge ${statusClass}">${statusLabel}</span></span>
                </div>
            </div>
            <div class="btn-chip" style="background: var(--bg-tertiary);">Open Topic &rarr;</div>
        `;
        
        item.addEventListener("click", () => {
            // Redirect to clean topic URL
            window.location.href = `/topic/${topic.slug}`;
        });
        
        listContainer.appendChild(item);
    });
}

