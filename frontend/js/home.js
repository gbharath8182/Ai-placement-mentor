(function () {
    function element(tag, className, content) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (content !== undefined) node.textContent = String(content);
        return node;
    }

    function validSlug(value) {
        return typeof value === 'string' && /^[a-zA-Z0-9_-]+$/.test(value);
    }

    async function publicFetch(path) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 12000);
        try {
            const response = await fetch(path, { signal: controller.signal, credentials: 'omit' });
            if (!response.ok) throw new Error('Catalog request failed');
            return await response.json();
        } finally {
            clearTimeout(timeout);
        }
    }

    function statusMessage(status, message, retry) {
        status.replaceChildren(element('span', '', message));
        if (retry) {
            const button = element('button', 'btn-secondary catalog-retry', 'Try again');
            button.type = 'button';
            button.addEventListener('click', retry);
            status.append(button);
        }
    }

    function topicList(topics, curated) {
        const list = element('ol', 'catalog-lessons');
        const ordered = [...topics].filter(topic => validSlug(topic.slug)).sort((first, second) => (Number(first.order) || 0) - (Number(second.order) || 0));
        ordered.forEach((topic, index) => {
            const item = element('li', 'catalog-lesson');
            const link = element('a', 'catalog-lesson-link');
            link.href = '/topic/' + encodeURIComponent(topic.slug);
            const number = element('span', 'lesson-index', String(index + 1).padStart(2, '0'));
            number.setAttribute('aria-hidden', 'true');
            const content = element('div', 'lesson-summary');
            content.append(element('h3', '', topic.title || topic.slug));
            if (topic.difficulty) content.append(element('span', 'lesson-difficulty', topic.difficulty));
            const arrow = element('span', 'lesson-arrow', '↗');
            arrow.setAttribute('aria-hidden', 'true');
            link.append(number, content, arrow);
            item.append(link);
            if (curated && Array.isArray(topic.objectives) && topic.objectives.length) {
                const objectives = element('ul', 'lesson-objectives');
                topic.objectives.forEach(objective => objectives.append(element('li', '', objective)));
                item.append(objectives);
            }
            if (curated && Array.isArray(topic.prerequisites)) {
                const prerequisites = element('p', 'lesson-prerequisites', topic.prerequisites.length ? 'Before this lesson: ' : 'No prerequisites — start here.');
                topic.prerequisites.forEach((slug, prerequisiteIndex) => {
                    if (prerequisiteIndex) prerequisites.append(document.createTextNode(', '));
                    const prerequisite = ordered.find(candidate => candidate.slug === slug);
                    if (prerequisite && validSlug(slug)) {
                        const prerequisiteLink = element('a', '', prerequisite.title || slug);
                        prerequisiteLink.href = '/topic/' + encodeURIComponent(slug);
                        prerequisites.append(prerequisiteLink);
                    } else {
                        prerequisites.append(document.createTextNode(String(slug)));
                    }
                });
                item.append(prerequisites);
            }
            list.append(item);
        });
        return list;
    }

    async function loadCurriculum() {
        const container = document.getElementById('curriculum-list');
        const status = document.getElementById('curriculum-status');
        container.setAttribute('aria-busy', 'true');
        statusMessage(status, 'Loading the curriculum…');
        try {
            const curriculum = await publicFetch('/curriculum');
            if (!Array.isArray(curriculum.domains) || !Array.isArray(curriculum.topics)) throw new Error('Invalid curriculum');
            const domains = [...curriculum.domains].sort((first, second) => Number(second.slug === 'python-foundations') - Number(first.slug === 'python-foundations'));
            const sections = domains.map(domain => {
                const section = element('section', 'curriculum-path');
                const header = element('div', 'curriculum-path-header');
                header.append(element('h3', '', domain.title || domain.slug));
                const version = domain.curriculum_version || domain.version || curriculum.version;
                if (version) header.append(element('span', 'preview-tag', 'Version ' + version));
                else if (domain.schema_version) header.append(element('span', 'preview-tag', 'Schema v' + domain.schema_version));
                section.append(header);
                if (domain.description) section.append(element('p', 'muted-text', domain.description));
                const topics = curriculum.topics.filter(topic => topic.domain_slug === domain.slug);
                section.append(topics.length ? topicList(topics, true) : element('p', 'empty-state', 'No lessons published in this path yet.'));
                return section;
            });
            container.replaceChildren(...sections);
            statusMessage(status, sections.length ? 'Choose a lesson below. Each path follows its published lesson order.' : 'The curated curriculum is not published yet. Explore the domains below.');
        } catch {
            statusMessage(status, 'The curated curriculum is temporarily unavailable. Published domains may still be available below.', loadCurriculum);
        } finally {
            container.setAttribute('aria-busy', 'false');
        }
    }

    function domainCard(domain, index) {
        const details = element('details', 'published-domain');
        const summary = element('summary');
        summary.append(element('span', 'domain-catalog-index', String(index + 1).padStart(2, '0')), element('span', 'published-domain-title', domain.title || domain.slug), element('span', 'domain-expand-label', 'View topics'));
        const content = element('div', 'published-domain-content');
        if (domain.description) content.append(element('p', 'muted-text', domain.description));
        const status = element('p', 'catalog-status');
        status.setAttribute('role', 'status');
        status.setAttribute('aria-live', 'polite');
        const list = element('div');
        content.append(status, list);
        details.append(summary, content);
        let state = 'idle';

        async function loadTopics() {
            if (state === 'loading' || state === 'loaded') return;
            state = 'loading';
            list.setAttribute('aria-busy', 'true');
            statusMessage(status, 'Loading published topics…');
            try {
                const topics = await publicFetch('/domains/' + encodeURIComponent(domain.slug) + '/topics');
                if (!Array.isArray(topics)) throw new Error('Invalid topics');
                const published = topics.filter(topic => validSlug(topic.slug));
                list.replaceChildren(topicList(published, false));
                statusMessage(status, published.length ? 'Select a topic to read its lesson.' : 'No topics published in this domain yet.');
                state = 'loaded';
            } catch {
                state = 'idle';
                statusMessage(status, 'Topics are temporarily unavailable.', loadTopics);
            } finally {
                list.setAttribute('aria-busy', 'false');
            }
        }

        details.addEventListener('toggle', function () {
            if (details.open) loadTopics();
        });
        return details;
    }

    async function loadDomains() {
        const container = document.getElementById('published-domains');
        const status = document.getElementById('domains-status');
        container.setAttribute('aria-busy', 'true');
        statusMessage(status, 'Loading published domains…');
        try {
            const response = await publicFetch('/domains');
            if (!Array.isArray(response)) throw new Error('Invalid domains');
            const domains = response.filter(domain => validSlug(domain.slug));
            container.replaceChildren(...domains.map(domainCard));
            statusMessage(status, domains.length ? 'Published content is available without an account.' : 'No learning domains are published yet.');
        } catch {
            statusMessage(status, 'Published domains are temporarily unavailable. You can still explore any curated paths above.', loadDomains);
        } finally {
            container.setAttribute('aria-busy', 'false');
        }
    }

    function initialize() {
        if (!document.getElementById('curriculum-list')) return;
        loadCurriculum();
        loadDomains();
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
    else initialize();
})();
