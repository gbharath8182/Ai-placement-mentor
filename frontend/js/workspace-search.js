(function () {
    const trigger = document.querySelector('.workspace-search-trigger');
    if (!trigger) return;
    const destinations = [
        ['Dashboard', '/dashboard', 'Your study queue and recent work'],
        ['Curriculum', '/learn', 'Public lessons and learning domains'],
        ['Learning paths', '/roadmap', 'Roadmaps and prerequisites'],
        ['Analytics', '/analytics', 'Activity and learning progress'],
        ['Code workspace', '/playground', 'Editor and remote code execution'],
        ['Reference library', '/cheatsheets', 'Books and quick references'],
        ['Aptitude practice', '/aptitude', 'Reasoning and quantitative questions'],
        ['Mock interviews', '/mock-interview', 'Text, camera and voice interview practice'],
        ['Resume studio', '/resume', 'Create and download a PDF resume'],
        ['Profile', '/profile', 'Your account and experience'],
    ];
    function element(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }
    const dialog = element('dialog', 'workspace-command');
    dialog.setAttribute('aria-labelledby', 'command-title');
    const header = element('div', 'command-header');
    const title = element('h2', '', 'Find your next step');
    title.id = 'command-title';
    const close = element('button', 'command-close', 'Close');
    close.type = 'button';
    header.append(title, close);
    const label = element('label', 'sr-only', 'Search tools and published lessons');
    label.htmlFor = 'command-input';
    const input = element('input', 'command-input');
    input.id = 'command-input';
    input.type = 'search';
    input.maxLength = 80;
    input.placeholder = 'Search tools, Python, data structures…';
    input.autocomplete = 'off';
    const status = element('p', 'command-status', 'Start with a tool, or type at least two characters to find lessons.');
    status.setAttribute('role', 'status');
    input.setAttribute('aria-describedby', 'command-status');
    status.id = 'command-status';
    const results = element('div', 'command-results');
    const footer = element('p', 'command-footer', '↑ ↓ Move between results · Enter Open · Esc Close');
    dialog.append(header, label, input, status, results, footer);
    document.body.appendChild(dialog);
    let timer;
    let controller;
    let generation = 0;
    let returnFocus;
    function link(titleText, href, detail, kind) {
        const anchor = element('a', 'command-result');
        anchor.href = href;
        const copy = element('span');
        copy.append(element('strong', '', titleText), element('small', '', detail));
        anchor.append(copy, element('span', 'command-kind', kind));
        return anchor;
    }
    function navigation(query) {
        const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
        return destinations.filter(([titleText, href, detail]) => terms.every(term => `${titleText} ${detail}`.toLowerCase().includes(term)));
    }
    function cancel() { clearTimeout(timer); controller?.abort(); generation += 1; }
    function render() {
        cancel();
        const current = generation;
        const query = input.value.trim();
        const tools = navigation(query);
        results.replaceChildren(...tools.map(([titleText, href, detail]) => link(titleText, href, detail, 'Tool')));
        if (query.length < 2) {
            status.textContent = 'Type at least two characters to search published lessons.';
            return;
        }
        status.textContent = 'Searching published lessons…';
        timer = setTimeout(async () => {
            const requestController = new AbortController();
            controller = requestController;
            const timeout = setTimeout(() => requestController.abort(), 10000);
            try {
                const response = await fetch(`/catalog/search?q=${encodeURIComponent(query)}`, { signal: requestController.signal, credentials: 'same-origin' });
                if (!response.ok) throw new Error('unavailable');
                const data = await response.json();
                if (current !== generation || !dialog.open) return;
                if (!Array.isArray(data.results)) throw new Error('unavailable');
                const lessons = data.results.filter(item => typeof item.slug === 'string' && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.slug));
                lessons.forEach(item => results.appendChild(link(item.title, `/topic/${encodeURIComponent(item.slug)}`, `${item.domain_slug.replaceAll('-', ' ')} · ${item.difficulty}`, 'Lesson')));
                const count = tools.length + lessons.length;
                status.textContent = `${count ? `${count} ${count === 1 ? 'result' : 'results'}.` : 'No matches. Try a subject such as Python, or a tool such as resume.'}${data.degraded ? ' Live catalog unavailable; only built-in lessons are shown.' : ''}`;
            } catch {
                if (current !== generation || !dialog.open) return;
                status.textContent = 'Lesson search is unavailable. Tools still work. Change your query to retry or browse the curriculum.';
                results.appendChild(link('Browse curriculum', '/learn', 'Explore the published catalog', 'Tool'));
            } finally { clearTimeout(timeout); }
        }, 240);
    }
    function open() {
        if (dialog.open || document.querySelector('dialog[open]')) return;
        returnFocus = document.activeElement;
        dialog.showModal();
        input.value = '';
        render();
        input.focus();
    }
    trigger.addEventListener('click', open);
    close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('close', () => { cancel(); if (returnFocus?.isConnected) returnFocus.focus(); });
    input.addEventListener('input', render);
    document.addEventListener('keydown', event => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); if (dialog.open) dialog.close(); else open(); }
    });
    dialog.addEventListener('keydown', event => {
        if (event.key === 'Escape') { event.preventDefault(); dialog.close(); return; }
        const anchors = [...results.querySelectorAll('a')];
        const index = anchors.indexOf(document.activeElement);
        if (event.key === 'ArrowDown' && anchors.length) { event.preventDefault(); anchors[(index + 1) % anchors.length].focus(); }
        else if (event.key === 'ArrowUp' && anchors.length) { event.preventDefault(); if (index <= 0) input.focus(); else anchors[index - 1].focus(); }
        else if (event.key === 'Enter' && document.activeElement === input && anchors.length) { event.preventDefault(); anchors[0].click(); }
    });
})();
