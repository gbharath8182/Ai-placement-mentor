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
        // Map slug to a funny icon
        let icon = "💻";
        if (domain.slug === "python") icon = "🐍";
        else if (domain.slug === "machine-learning") icon = "🤖";
        else if (domain.slug === "dsa") icon = "📊";
        
        const card = document.createElement("div");
        card.className = "domain-card glass-panel";
        card.innerHTML = `
            <span class="domain-icon">${icon}</span>
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
