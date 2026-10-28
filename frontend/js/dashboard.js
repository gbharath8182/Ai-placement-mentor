let dashboardDomains = [];
let activeTopicRequest = 0;
let activeDomainCard = null;

document.addEventListener('DOMContentLoaded', async () => {
    const user = getUser();
    if (user) {
        const account = document.getElementById('user-name');
        if (account) account.textContent = user.name;
        document.getElementById('hero-user-name').textContent = user.name;
        const level = document.getElementById('user-exp-badge');
        if (level) level.textContent = user.profile?.experience_level || 'fresher';
    }
    document.getElementById('domain-search')?.addEventListener('input', event => {
        const query = event.target.value.trim().toLowerCase();
        renderDomains(dashboardDomains.filter(domain => `${domain.title} ${domain.description}`.toLowerCase().includes(query)));
    });
    document.getElementById('close-drawer-btn').addEventListener('click', () => {
        activeTopicRequest += 1;
        document.getElementById('topics-drawer').style.display = 'none';
        document.querySelectorAll('.domain-card').forEach(card => card.setAttribute('aria-expanded', 'false'));
        if (activeDomainCard?.isConnected) activeDomainCard.focus();
        else document.getElementById('domain-search').focus();
    });
    await Promise.allSettled([loadDashboardDomains(), loadDashboardStats(user), loadStudyOverview()]);
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
        } else document.getElementById('stats-completed').textContent = 'Unavailable';
        if (responses[1].ok) {
            const streak = await responses[1].json();
            const days = Number(streak.current_streak) || 0;
            document.getElementById('stats-streak').textContent = `${days} ${days === 1 ? 'day' : 'days'}`;
        } else document.getElementById('stats-streak').textContent = 'Unavailable';
    } catch {
        document.getElementById('stats-completed').textContent = 'Unavailable';
        document.getElementById('stats-streak').textContent = 'Unavailable';
    }
}

function studyLink(item, label, className = 'study-row') {
    const link = dashboardElement('a', className);
    link.href = `/topic/${encodeURIComponent(item.slug)}`;
    link.append(dashboardElement('strong', '', label || item.title), dashboardElement('span', '', item.reason || 'Open lesson'));
    return link;
}

async function loadStudyOverview() {
    const overview = document.getElementById('study-overview');
    const main = document.getElementById('study-main');
    const reviews = document.getElementById('study-reviews');
    const note = document.getElementById('study-note');
    overview.setAttribute('aria-busy', 'true');
    note.textContent = '';
    try {
        const response = await authFetch('/workspace/overview', { signal: AbortSignal.timeout(15000) });
        if (!response.ok) throw new Error(response.headers.get('x-request-id') || '');
        const data = await response.json();
        if (!Array.isArray(data.continue) || !Array.isArray(data.reviews)) throw new Error('');
        const next = data.continue[0] || data.reviews[0] || data.suggested;
        const isNew = data.has_history === false;
        main.replaceChildren(dashboardElement('p', 'workspace-eyebrow', data.continue.length ? 'Pick up where you left off' : data.reviews.length ? 'Recommended review' : isNew ? 'Your first study session' : 'Explore the curriculum'));
        main.append(dashboardElement('h2', '', next?.title || 'Choose a learning path'), dashboardElement('p', 'study-description', next?.reason || (isNew ? 'Start with a short lesson. Your queue will fill as you study and submit assessments.' : 'No pending reviews in your recent evidence. Explore another lesson or practice an interview.')));
        const action = dashboardElement('a', 'btn-primary', data.continue.length ? 'Continue lesson →' : data.reviews.length ? 'Review concept →' : isNew ? 'Start the first lesson →' : 'Browse lessons →');
        action.href = next && (data.continue.length || data.reviews.length || isNew) ? `/topic/${encodeURIComponent(next.slug)}` : '/learn';
        main.appendChild(action);
        if (data.continue.length > 1) {
            const more = dashboardElement('div', 'study-more');
            more.appendChild(dashboardElement('p', 'study-small-label', 'Also in progress'));
            data.continue.slice(1).forEach(item => more.appendChild(studyLink(item)));
            main.appendChild(more);
        }
        reviews.replaceChildren();
        document.getElementById('review-count').textContent = String(data.counts.review);
        document.getElementById('stats-mastered').textContent = String(data.counts.mastered);
        if (!data.reviews.length) {
            reviews.append(dashboardElement('p', 'review-clear-title', 'Nothing to reassess yet.'), dashboardElement('p', 'study-description', 'Missed checks and evidence that needs refreshing appear here. This is a study aid, not an interview-readiness score.'));
            const explore = dashboardElement('a', 'study-text-link', 'Find a lesson →');
            explore.href = '/learn';
            reviews.appendChild(explore);
        } else data.reviews.forEach(item => reviews.appendChild(studyLink(item)));
        note.textContent = `${data.limited ? `Showing your ${data.window} most recently updated records per category. ` : ''}${data.unavailable_lessons ? 'Some saved lessons are unavailable in the current catalog. ' : ''}Mastery uses fresh assessment evidence, not reading time. Completed topics and mastery are different measures.`;
        document.getElementById('runner-note').textContent = data.capabilities.runner_configured ? 'Remote runner configured; availability checked when you run.' : 'Editor available. Remote execution is not configured yet.';
        if (!data.capabilities.ai_configured) note.textContent += ' AI tools are not configured on this instance.';
    } catch (error) {
        main.replaceChildren(dashboardElement('p', 'workspace-eyebrow', 'Study queue'), dashboardElement('h2', '', 'Your queue is temporarily unavailable.'), dashboardElement('p', 'study-description', 'Your saved work has not been changed. Retry, or browse lessons below.'));
        const retry = dashboardElement('button', 'btn-secondary', 'Retry study queue');
        retry.type = 'button';
        retry.addEventListener('click', loadStudyOverview);
        main.appendChild(retry);
        reviews.replaceChildren(dashboardElement('p', 'study-description', 'Assessment history could not be loaded. We won’t replace it with zeroes.'));
        document.getElementById('review-count').textContent = '—';
        document.getElementById('stats-mastered').textContent = '—';
        if (/^[a-f0-9]{32}$/.test(error.message)) note.textContent = `Support reference: ${error.message}`;
    } finally { overview.setAttribute('aria-busy', 'false'); }
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
            activeDomainCard = card;
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

