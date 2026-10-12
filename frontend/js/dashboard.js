let dashboardDomains = [];
let activeTopicRequest = 0;

document.addEventListener('DOMContentLoaded', async () => {
    const user = getUser();
    if (user) {
        document.getElementById('user-name').textContent = user.name;
        document.getElementById('hero-user-name').textContent = user.name;
        document.getElementById('user-exp-badge').textContent = user.profile?.experience_level || 'fresher';
    }
    document.getElementById('domain-search')?.addEventListener('input', event => {
        const query = event.target.value.trim().toLowerCase();
        renderDomains(dashboardDomains.filter(domain => `${domain.title} ${domain.description}`.toLowerCase().includes(query)));
    });
    document.getElementById('close-drawer-btn').addEventListener('click', () => {
        activeTopicRequest += 1;
        document.getElementById('topics-drawer').style.display = 'none';
        document.querySelectorAll('.domain-card').forEach(card => card.setAttribute('aria-expanded', 'false'));
        document.querySelector('.domain-card')?.focus();
    });
    await Promise.allSettled([loadDashboardDomains(), loadDashboardStats(user)]);
});

function dashboardElement(tag, className, text) {
    const result = document.createElement(tag);
    if (className) result.className = className;
    if (text !== undefined) result.textContent = text;
    return result;
}

async function loadDashboardDomains() {
    const grid = document.getElementById('domain-grid');
    try {
        const response = await authFetch('/domains');
        if (!response.ok) throw new Error('unavailable');
        dashboardDomains = await response.json();
        renderDomains(dashboardDomains);
    } catch {
        const notice = dashboardElement('div', 'workspace-empty', 'Learning paths could not be loaded. Your saved progress is unchanged. ');
        const retry = dashboardElement('button', 'btn-secondary', 'Retry');
        retry.type = 'button';
        retry.addEventListener('click', loadDashboardDomains);
        notice.appendChild(retry);
        grid.replaceChildren(notice);
    }
}

async function loadDashboardStats(user) {
    if (!user?.id) return;
    try {
        const responses = await Promise.all([authFetch(`/progress/${encodeURIComponent(user.id)}`), authFetch('/activity/streak')]);
        if (responses[0].ok) {
            const progress = await responses[0].json();
            document.getElementById('stats-completed').textContent = String(progress.filter(item => item.status === 'completed').length);
        }
        if (responses[1].ok) {
            const streak = await responses[1].json();
            const days = Number(streak.current_streak) || 0;
            document.getElementById('stats-streak').textContent = `${days} ${days === 1 ? 'day' : 'days'}`;
        }
    } catch { }
}

function renderDomains(domains) {
    const grid = document.getElementById('domain-grid');
    grid.replaceChildren();
    if (!domains.length) {
        grid.appendChild(dashboardElement('p', 'workspace-empty', dashboardDomains.length ? 'No paths match your search. Try a different subject.' : 'No curriculum is available yet. Please check back later.'));
        return;
    }
    domains.forEach(domain => {
        const card = dashboardElement('button', 'domain-card glass-panel');
        card.type = 'button';
        card.setAttribute('aria-controls', 'topics-drawer');
        card.setAttribute('aria-expanded', 'false');
        card.append(dashboardElement('span', 'domain-card-kicker', 'Learning path'), dashboardElement('span', 'domain-name', domain.title), dashboardElement('span', 'domain-desc', domain.description));
        const footer = dashboardElement('span', 'domain-card-foot');
        const count = Array.isArray(domain.topics) ? domain.topics.length : 0;
        footer.append(dashboardElement('span', '', count ? `${count} ${count === 1 ? 'lesson' : 'lessons'}` : 'Explore the curriculum'), dashboardElement('strong', '', 'View path →'));
        card.appendChild(footer);
        card.addEventListener('click', () => {
            grid.querySelectorAll('.domain-card').forEach(item => item.setAttribute('aria-expanded', 'false'));
            card.setAttribute('aria-expanded', 'true');
            fetchAndShowTopics(domain);
        });
        grid.appendChild(card);
    });
}

async function fetchAndShowTopics(domain) {
    const request = ++activeTopicRequest;
    const drawer = document.getElementById('topics-drawer');
    const list = document.getElementById('topic-list');
    const title = document.getElementById('drawer-domain-title');
    title.textContent = domain.title;
    title.setAttribute('tabindex', '-1');
    drawer.style.display = 'block';
    list.replaceChildren(dashboardElement('p', 'workspace-empty', 'Loading lessons…'));
    drawer.scrollIntoView({ behavior: 'auto', block: 'start' });
    title.focus({ preventScroll: true });
    try {
        const response = await authFetch(`/domains/${encodeURIComponent(domain.slug)}/topics`);
        if (!response.ok) throw new Error('unavailable');
        const topics = await response.json();
        const progressMap = {};
        const user = getUser();
        if (user?.id) {
            try {
                const progressResponse = await authFetch(`/progress/${encodeURIComponent(user.id)}`);
                if (progressResponse.ok) (await progressResponse.json()).forEach(progress => { progressMap[progress.topic_slug] = progress.status; });
            } catch { }
        }
        if (request === activeTopicRequest) renderTopics(topics, progressMap);
    } catch {
        if (request !== activeTopicRequest) return;
        const notice = dashboardElement('div', 'workspace-empty', 'These lessons are temporarily unavailable. ');
        const retry = dashboardElement('button', 'btn-secondary', 'Retry');
        retry.type = 'button';
        retry.addEventListener('click', () => fetchAndShowTopics(domain));
        notice.appendChild(retry);
        list.replaceChildren(notice);
    }
}

function renderTopics(topics, progressMap) {
    const list = document.getElementById('topic-list');
    list.replaceChildren();
    if (!topics.length) { list.appendChild(dashboardElement('p', 'workspace-empty', 'This path has no published lessons yet.')); return; }
    topics.forEach(topic => {
        const status = progressMap[topic.slug] || 'not_started';
        const item = dashboardElement('a', 'topic-item');
        item.href = `/topic/${encodeURIComponent(topic.slug)}`;
        const information = dashboardElement('div', 'topic-info');
        information.appendChild(dashboardElement('span', 'topic-title', topic.title));
        const metadata = dashboardElement('div', 'topic-meta');
        const difficulty = ['beginner', 'intermediate', 'advanced'].includes(topic.difficulty) ? topic.difficulty : 'beginner';
        const statusClass = status === 'completed' ? 'status-completed' : status === 'in_progress' ? 'status-in-progress' : 'status-not-started';
        const label = status === 'completed' ? 'Completed' : status === 'in_progress' ? 'In progress' : 'Not started';
        metadata.append(dashboardElement('span', `problem-difficulty diff-${difficulty}`, difficulty), dashboardElement('span', `status-badge ${statusClass}`, label));
        information.appendChild(metadata);
        item.append(information, dashboardElement('span', 'domain-action', 'Study lesson →'));
        list.appendChild(item);
    });
}

