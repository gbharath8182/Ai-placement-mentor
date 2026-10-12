const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

class FakeElement {
    constructor(document, tagName = 'div') {
        this.document = document;
        this.tagName = tagName;
        this.children = [];
        this.listeners = new Map();
        this.attributes = new Map();
        this.selectors = new Map();
        this.value = '';
        this.disabled = false;
        this.hidden = false;
        this.html = '';
        this.text = '';
        const classes = new Set();
        this.classList = {
            add: (...names) => names.forEach(name => classes.add(name)),
            remove: (...names) => names.forEach(name => classes.delete(name)),
            contains: name => classes.has(name),
        };
    }

    set id(value) { this.identifier = value; this.document.elements.set(value, this); }
    get id() { return this.identifier; }
    set textContent(value) { this.text = String(value); this.html = ''; this.children = []; }
    get textContent() { return this.text + this.children.map(child => child.textContent).join(''); }
    set innerHTML(value) { this.html = String(value); this.text = ''; this.children = []; }
    get innerHTML() { return this.html; }
    setAttribute(name, value) { this.attributes.set(name, String(value)); }
    getAttribute(name) { return this.attributes.get(name) ?? null; }
    addEventListener(name, listener) {
        if (!this.listeners.has(name)) this.listeners.set(name, []);
        this.listeners.get(name).push(listener);
    }
    async emit(name, event = {}) {
        for (const listener of this.listeners.get(name) || []) {
            await listener({ preventDefault() {}, target: this, ...event });
        }
    }
    appendChild(child) { child.parentElement = this; this.children.push(child); return child; }
    append(...children) { children.forEach(child => this.appendChild(child)); }
    replaceChildren(...children) { this.text = ''; this.html = ''; this.children = []; children.forEach(child => this.appendChild(child)); }
    remove() { this.parentElement.children = this.parentElement.children.filter(child => child !== this); }
    querySelector(selector) { return this.selectors.get(selector) || null; }
    querySelectorAll(selector) {
        if (selector === '.resume-project') return this.children.filter(child => child.className === 'resume-project');
        return this.selectors.get(selector) || [];
    }
}

function browser({ pathname = '/topic/python-foundations', storage = {}, fetch } = {}) {
    const document = new FakeElement(null, 'document');
    document.document = document;
    document.elements = new Map();
    document.createElement = tagName => new FakeElement(document, tagName);
    document.getElementById = identifier => document.elements.get(identifier) || null;
    document.querySelectorAll = selector => document.selectors.get(selector) || [];
    const window = new FakeElement(document, 'window');
    window.location = { pathname, href: pathname };
    const values = new Map(Object.entries(storage));
    const context = vm.createContext({
        document, window, AbortController, TextDecoder, TextEncoder, FormData,
        Blob, URL, currentTopicSlug: 'python-foundations',
        console: { log() {}, warn() {}, error() {} },
        localStorage: {
            getItem: key => values.get(key) ?? null,
            setItem: (key, value) => values.set(key, String(value)),
            removeItem: key => values.delete(key),
            clear() { throw new Error('Storage-wide clearing destroys user preferences'); },
        },
        fetch: fetch || (async () => { throw new Error('Unexpected network access in smoke test'); }),
    });
    const element = (identifier, tagName) => {
        const result = document.createElement(tagName);
        result.id = identifier;
        return result;
    };
    const load = filename => {
        const sourcePath = path.join(__dirname, '..', 'frontend', 'js', filename);
        vm.runInContext(readFileSync(sourcePath, 'utf8'), context, { filename: sourcePath, timeout: 1000 });
    };
    return { context, document, window, values, element, load };
}

function deferred() {
    let resolve;
    const promise = new Promise(complete => { resolve = complete; });
    return { promise, resolve };
}

function chatBrowser(authFetch) {
    const harness = browser();
    const parent = harness.element('chat-panel');
    parent.appendChild(harness.element('ai-chat-form', 'form'));
    harness.element('ai-chat-logs');
    harness.element('ai-status-text');
    harness.element('chat-input', 'input');
    harness.element('subtopic-title-badge').textContent = 'Variables';
    const buttons = ['chat-send-btn', 'chip-explain-simply', 'chip-deep-dive', 'chip-quiz'].map(identifier => harness.element(identifier, 'button'));
    harness.document.selectors.set('.ai-actions-bar button, #chat-send-btn', buttons);
    harness.context.authFetch = authFetch;
    harness.load('ai-sidebar.js');
    harness.ready = harness.document.emit('DOMContentLoaded');
    harness.bubbles = () => harness.document.getElementById('ai-chat-logs').children;
    harness.assistant = () => harness.bubbles().at(-1);
    harness.assertIdle = () => {
        assert.equal(harness.document.getElementById('ai-stop-btn').hidden, true);
        assert.equal(harness.document.getElementById('ai-status-text').textContent, 'Lesson companion');
        assert.ok(buttons.every(button => !button.disabled));
        assert.equal(harness.assistant().getAttribute('aria-busy'), 'false');
    };
    return harness;
}

test('saved tutor history restores bounded escaped user-scoped messages', async () => {
    const harness = chatBrowser(async url => {
        assert.equal(url, '/ai/history/python-foundations');
        return { ok: true, json: async () => ({ messages: [
            { role: 'system', content: 'must not render' },
            { role: 'user', content: '<script>history question</script>' },
            { role: 'assistant', content: '**Saved answer** <img onerror=alert(1)>' },
        ] }) };
    });
    harness.context.getAccessToken = () => 'test-access';
    await harness.ready;
    await harness.context.restoreTutorHistory();
    assert.equal(harness.bubbles().length, 2);
    assert.equal(harness.bubbles()[0].textContent, '<script>history question</script>');
    assert.ok(harness.assistant().innerHTML.includes('<strong>Saved answer</strong>'));
    assert.ok(harness.assistant().innerHTML.includes('&lt;img'));
    harness.assertIdle();
});

test('history fetch failure leaves a safe notice and usable tutor controls', async () => {
    const harness = chatBrowser(async () => { throw new Error('private upstream failure'); });
    harness.context.getAccessToken = () => 'test-access';
    await harness.ready;
    await harness.context.restoreTutorHistory();
    assert.equal(harness.bubbles().length, 1);
    assert.ok(harness.bubbles()[0].textContent.includes('could not be loaded'));
    assert.ok(!harness.bubbles()[0].textContent.includes('private upstream'));
    assert.equal(harness.document.getElementById('chat-send-btn').disabled, false);
});

test('lesson checks use explicit identity or exact legacy coordinates, not repeated question text', () => {
    const harness = browser();
    harness.load('topic.js');
    vm.runInContext(`lessonChecks = [
        {block_id: 'first', question: 'Repeated question', subtopic_index: 0, block_index: 3},
        {block_id: 'second', question: 'Repeated question', subtopic_index: 1, block_index: 3}
    ]`, harness.context);
    const resolve = harness.context.resolveLessonCheck;
    assert.equal(resolve({block_id: 'second'}, 0, 3).block_id, 'second');
    assert.equal(resolve({question: 'Repeated question'}, 1, 3).block_id, 'second');
    assert.equal(resolve({question: 'Repeated question'}, 2, 3), undefined);
    assert.equal(resolve({id: 'missing'}, 1, 3), undefined);
});

test('dashboard renders keyboard-native domain cards without icons or unsafe HTML', () => {
    const harness = browser({ pathname: '/dashboard' });
    const grid = harness.element('domain-grid');
    harness.load('dashboard.js');
    harness.context.renderDomains([{ slug: 'python', title: '<img src=x onerror=alert(1)>', description: 'Learn <script>without injection</script>', topics: ['intro'] }]);
    assert.equal(grid.children.length, 1);
    const card = grid.children[0];
    assert.equal(card.tagName, 'button');
    assert.equal(card.type, 'button');
    assert.equal(card.getAttribute('aria-controls'), 'topics-drawer');
    assert.equal(card.getAttribute('aria-expanded'), 'false');
    assert.equal(card.innerHTML, '');
    assert.ok(card.textContent.includes('<img src=x onerror=alert(1)>'));
    assert.ok(card.textContent.includes('1 lesson'));
    assert.ok(!card.children.some(child => child.tagName === 'svg'));
});

test('dashboard topic links encode slugs and use bounded visual states', () => {
    const harness = browser({ pathname: '/dashboard' });
    const list = harness.element('topic-list');
    harness.load('dashboard.js');
    harness.context.renderTopics([{ slug: 'unsafe?next=/private', title: '<script>Lesson title</script>', difficulty: 'bad-class injection' }], {});
    const link = list.children[0];
    assert.equal(link.tagName, 'a');
    assert.equal(link.href, '/topic/unsafe%3Fnext%3D%2Fprivate');
    assert.equal(link.innerHTML, '');
    assert.ok(link.textContent.includes('<script>Lesson title</script>'));
    assert.ok(link.textContent.includes('beginner'));
    assert.ok(link.textContent.includes('Not started'));
});

test('dashboard provides a genuine empty state instead of placeholder cards', () => {
    const harness = browser({ pathname: '/dashboard' });
    const grid = harness.element('domain-grid');
    harness.load('dashboard.js');
    harness.context.renderDomains([]);
    assert.equal(grid.children.length, 1);
    assert.ok(grid.children[0].textContent.includes('No curriculum'));
});

function streamResponse(chunks, readOverride) {
    const stats = { reads: 0, cancellations: 0, releases: 0 };
    const reader = {
        async read() {
            stats.reads += 1;
            if (readOverride) return readOverride(stats.reads);
            const value = chunks[stats.reads - 1];
            return value === undefined ? { done: true } : { done: false, value };
        },
        async cancel() { stats.cancellations += 1; },
        releaseLock() { stats.releases += 1; },
    };
    return { response: { ok: true, body: { getReader: () => reader } }, stats };
}

function delta(content) {
    return `data: ${JSON.stringify({ choices: [{ delta: { content } }] })}\n\n`;
}

const encoder = new TextEncoder();

for (const pathname of ['/', '/learn', '/topic/python-foundations', '/forgot-password', '/reset-password']) {
    test(`anonymous auth guard leaves public ${pathname} accessible`, async () => {
        const harness = browser({ pathname });
        harness.load('auth.js');
        await harness.document.emit('DOMContentLoaded');
        assert.equal(harness.window.location.href, pathname);
    });
}

for (const pathname of ['/dashboard', '/resume', '/analytics', '/mock-interview']) {
    test(`anonymous auth guard redirects protected ${pathname}`, async () => {
        const harness = browser({ pathname });
        harness.load('auth.js');
        await harness.document.emit('DOMContentLoaded');
        assert.equal(harness.window.location.href, '/login');
    });
}

test('authenticated guard preserves public/protected routes but redirects login and signup', () => {
    const harness = browser({ storage: { access_token: 'test-access' } });
    harness.load('auth.js');
    for (const pathname of ['/', '/learn', '/topic/python-foundations', '/dashboard', '/login', '/signup']) {
        harness.window.location = { pathname, href: pathname };
        harness.context.checkAuth();
        assert.equal(harness.window.location.href, ['/login', '/signup'].includes(pathname) ? '/dashboard' : pathname);
    }
});

for (const failure of ['http', 'network', 'invalid-json']) {
    test(`failed refresh (${failure}) clears only auth storage`, async () => {
        const harness = browser({
            storage: { access_token: 'expired-test', refresh_token: 'test-refresh', user: '{}', theme: 'light', editor_theme: 'dark' },
            fetch: async (url, options) => {
                assert.equal(url, '/auth/refresh');
                assert.deepEqual(JSON.parse(options.body), { refresh_token: 'test-refresh' });
                if (failure === 'network') throw new Error('test offline');
                return { ok: failure === 'invalid-json', json: async () => { throw new SyntaxError('invalid test response'); } };
            },
        });
        harness.load('auth.js');
        assert.equal(await harness.context.attemptRefresh(), false);
        assert.deepEqual(Object.fromEntries(harness.values), { theme: 'light', editor_theme: 'dark' });
    });
}

test('authFetch refreshes once for concurrent 401s and retries with the new bearer token', async () => {
    const refresh = deferred();
    const calls = [];
    const harness = browser({
        storage: { access_token: 'expired-test', refresh_token: 'test-refresh', theme: 'light' },
        fetch: async (url, options) => {
            calls.push({ url, authorization: options.headers.Authorization });
            if (url === '/auth/refresh') return refresh.promise;
            return { status: options.headers.Authorization === 'Bearer new-test' ? 200 : 401 };
        },
    });
    harness.load('auth.js');
    const first = harness.context.authFetch('/protected/first');
    const second = harness.context.authFetch('/protected/second');
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(calls.filter(call => call.url === '/auth/refresh').length, 1);
    refresh.resolve({ ok: true, json: async () => ({ access_token: 'new-test', refresh_token: 'new-refresh-test' }) });
    assert.deepEqual((await Promise.all([first, second])).map(response => response.status), [200, 200]);
    assert.equal(calls.filter(call => call.authorization === 'Bearer new-test').length, 2);
    assert.equal(harness.values.get('refresh_token'), 'new-refresh-test');
    assert.equal(harness.values.get('theme'), 'light');
});

test('failed authFetch refresh logs out without deleting theme preferences', async () => {
    const calls = [];
    const harness = browser({
        pathname: '/dashboard',
        storage: { access_token: 'expired-test', refresh_token: 'test-refresh', user: '{}', theme: 'dark' },
        fetch: async url => { calls.push(url); return { ok: false, status: 401 }; },
    });
    harness.load('auth.js');
    assert.equal((await harness.context.authFetch('/protected')).status, 401);
    await new Promise(resolve => setImmediate(resolve));
    assert.deepEqual(calls, ['/protected', '/auth/refresh', '/auth/logout']);
    assert.equal(harness.window.location.href, '/login');
    assert.deepEqual(Object.fromEntries(harness.values), { theme: 'dark' });
});

test('sidebar decodes byte-fragmented UTF-8 SSE, escapes HTML, and consumes DONE', async () => {
    const wire = `: heartbeat\r\n${delta('Hello 🧠 ')}${delta('<img src=x onerror=alert(1)> **safe**')}${delta('\n```js\n<script>alert(1)</script>\n```')}data: [DONE]\r\n\r\n`;
    const chunks = Array.from(encoder.encode(wire), byte => Uint8Array.of(byte));
    const stream = streamResponse(chunks);
    const requests = [];
    const harness = chatBrowser(async (url, options) => { requests.push({ url, options }); return stream.response; });
    await harness.ready;
    await harness.context.sendUserMessage('<svg onload=alert(1)>');
    assert.equal(requests[0].url, '/ai/chat');
    assert.equal(requests[0].options.body.topic_slug, 'python-foundations');
    assert.equal(requests[0].options.body.subtopic_title, 'Variables');
    assert.equal(harness.bubbles()[0].textContent, '<svg onload=alert(1)>');
    assert.equal(harness.bubbles()[0].innerHTML, '');
    const html = harness.assistant().innerHTML;
    assert.match(html, /Hello 🧠/);
    assert.match(html, /&lt;img src=x onerror=alert\(1\)&gt; <strong>safe<\/strong>/);
    assert.match(html, /<pre><code>&lt;script&gt;alert\(1\)&lt;\/script&gt;<\/code><\/pre>/);
    assert.doesNotMatch(html, /<img|<script|data:|choices|\[DONE\]/);
    assert.equal(harness.assistant().children.length, 0);
    assert.equal(stream.stats.cancellations, 1);
    assert.equal(stream.stats.releases, 1);
    harness.assertIdle();
});

test('DONE stops further reader calls and releases the stream', async () => {
    const stream = streamResponse([encoder.encode(delta('Complete.') + 'data: [DONE]\n\n'), encoder.encode(delta('Do not render this.'))]);
    const harness = chatBrowser(async () => stream.response);
    await harness.ready;
    await harness.context.sendUserMessage('test question');
    assert.equal(harness.assistant().innerHTML, 'Complete.');
    assert.equal(stream.stats.reads, 1);
    assert.equal(stream.stats.cancellations, 1);
    assert.equal(stream.stats.releases, 1);
    harness.assertIdle();
});

test('premature SSE EOF preserves partial text and offers a retry', async () => {
    const stream = streamResponse([encoder.encode(delta('Partial reply'))]);
    const harness = chatBrowser(async () => stream.response);
    await harness.ready;
    await harness.context.sendUserMessage('test question');
    assert.equal(harness.assistant().innerHTML, 'Partial reply');
    assert.equal(harness.assistant().children[0].textContent, 'The reply was interrupted. Please retry.');
    assert.equal(harness.assistant().children[1].textContent, 'Retry');
    harness.assertIdle();
});

test('SSE flushes a final unterminated DONE record at EOF', async () => {
    const stream = streamResponse([encoder.encode(delta('Finished') + 'data: [DO'), encoder.encode('NE]')]);
    const harness = chatBrowser(async () => stream.response);
    await harness.ready;
    await harness.context.sendUserMessage('test question');
    assert.equal(harness.assistant().innerHTML, 'Finished');
    assert.equal(harness.assistant().children.length, 0);
    assert.equal(stream.stats.cancellations, 1);
    harness.assertIdle();
});

test('Retry starts a new request after a recoverable error', async () => {
    let requests = 0;
    const stream = streamResponse([encoder.encode(delta('Recovered') + 'data: [DONE]\n\n')]);
    const harness = chatBrowser(async () => {
        requests += 1;
        return requests === 1
            ? { ok: false, json: async () => ({ error: { code: 'timeout', message: 'Please retry.', retryable: true } }) }
            : stream.response;
    });
    await harness.ready;
    await harness.context.sendUserMessage('test question');
    const retry = harness.assistant().children[1];
    assert.equal(retry.textContent, 'Retry');
    await retry.emit('click');
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(requests, 2);
    assert.equal(harness.bubbles().length, 4);
    assert.equal(harness.assistant().innerHTML, 'Recovered');
    harness.assertIdle();
});

for (const payload of [
    { detail: '<script>private server traceback</script>' },
    { error: { code: 'unknown', message: '<img src=x onerror=alert(1)>', retryable: false } },
    { error: { code: 'service', message: { raw: 'private upstream JSON' } } },
]) {
    test(`sidebar sanitizes untrusted HTTP error shape ${JSON.stringify(payload)}`, async () => {
        const harness = chatBrowser(async () => ({ ok: false, json: async () => payload }));
        await harness.ready;
        await harness.context.sendUserMessage('test question');
        assert.equal(harness.assistant().children[0].textContent, 'The assistant is temporarily unavailable. Please retry shortly.');
        assert.equal(harness.assistant().innerHTML, '');
        assert.doesNotMatch(harness.assistant().textContent, /script|onerror|upstream|traceback/);
        harness.assertIdle();
    });
}

test('classified SSE errors render as text rather than raw JSON or executable HTML', async () => {
    const message = '<img src=x onerror=alert(1)> Assistant is busy.';
    const stream = streamResponse([encoder.encode(`data: ${JSON.stringify({ error: { code: 'rate_limit', message, retryable: false } })}\n\n`)]);
    const harness = chatBrowser(async () => stream.response);
    await harness.ready;
    await harness.context.sendUserMessage('test question');
    const notice = harness.assistant().children[0];
    assert.equal(notice.textContent, message);
    assert.equal(notice.innerHTML, '');
    assert.equal(harness.assistant().children.length, 1);
    assert.equal(stream.stats.reads, 1);
    assert.equal(stream.stats.cancellations, 1);
    harness.assertIdle();
});

test('malformed SSE never exposes raw payloads or parser errors', async () => {
    const stream = streamResponse([encoder.encode('data: {private traceback <script>bad()</script>\n\n')]);
    const harness = chatBrowser(async () => stream.response);
    await harness.ready;
    await harness.context.sendUserMessage('test question');
    assert.equal(harness.assistant().children[0].textContent, 'The connection was interrupted. Please retry.');
    assert.equal(harness.assistant().innerHTML, '');
    assert.doesNotMatch(harness.assistant().textContent, /traceback|script|SyntaxError/);
    assert.equal(stream.stats.releases, 1);
    harness.assertIdle();
});

for (const trigger of ['stop', 'pagehide']) {
    test(`${trigger} aborts an active reply and resets busy controls`, { timeout: 2000 }, async () => {
        const started = deferred();
        let signal;
        let requests = 0;
        const stream = streamResponse([], () => new Promise((resolve, reject) => {
            started.resolve();
            signal.addEventListener('abort', () => reject(Object.assign(new Error('test abort'), { name: 'AbortError' })), { once: true });
        }));
        const harness = chatBrowser(async (url, options) => { requests += 1; signal = options.signal; return stream.response; });
        await harness.ready;
        const reply = harness.context.sendUserMessage('test question');
        await started.promise;
        assert.equal(harness.document.getElementById('chat-send-btn').disabled, true);
        assert.equal(harness.document.getElementById('ai-stop-btn').hidden, false);
        await harness.context.sendUserMessage('duplicate while busy');
        assert.equal(requests, 1);
        assert.equal(harness.bubbles().length, 2);
        if (trigger === 'stop') await harness.document.getElementById('ai-stop-btn').emit('click');
        else await harness.window.emit('pagehide');
        await reply;
        assert.equal(signal.aborted, true);
        assert.equal(harness.assistant().children[0].textContent, 'Reply stopped.');
        assert.equal(stream.stats.cancellations, 1);
        assert.equal(stream.stats.releases, 1);
        harness.assertIdle();
    });
}

test('explain failures sanitize unknown error objects and reset controls', async () => {
    const harness = chatBrowser(async () => ({ ok: false, json: async () => ({ detail: '<script>server failure</script>' }) }));
    await harness.ready;
    await harness.document.getElementById('chip-explain-simply').emit('click');
    assert.equal(harness.bubbles()[0].textContent, 'Explain Simply requested.');
    assert.equal(harness.assistant().children[0].textContent, 'The assistant is temporarily unavailable. Please retry shortly.');
    assert.equal(harness.assistant().innerHTML, '');
    harness.assertIdle();
});

function resumeBrowser(documentData, libraries = {}) {
    const harness = browser();
    const form = harness.element('resume-form', 'form');
    const submit = harness.element('resume-submit', 'button');
    form.selectors.set('button[type=submit]', submit);
    harness.element('projects');
    const template = harness.element('project-template', 'template');
    template.content = { cloneNode() {
        const card = harness.document.createElement('section');
        card.className = 'resume-project';
        card.selectors.set('.resume-remove', harness.document.createElement('button'));
        for (const field of ['title', 'description', 'technologies', 'github_url', 'live_url']) {
            const input = harness.document.createElement('input');
            input.value = field === 'title' ? 'Test project' : '';
            card.selectors.set(`[data-project="${field}"]`, input);
        }
        return card;
    } };
    for (const identifier of ['add-project', 'resume-status', 'resume-output', 'download-resume']) harness.element(identifier);
    harness.context.FormData = class {
        entries() { return Object.entries({ full_name: 'Test Learner', skills: 'Python, SQL', achievements: 'Built a test project' })[Symbol.iterator](); }
    };
    Object.assign(harness.context, libraries);
    Object.assign(harness.window, libraries);
    harness.context.authFetch = async (url, options) => {
        assert.equal(url, '/resume/generate');
        assert.equal(options.body.full_name, 'Test Learner');
        assert.equal(JSON.stringify(options.body.skills), JSON.stringify(['Python', 'SQL']));
        assert.equal(options.body.projects[0].title, 'Test project');
        return { ok: true, json: async () => ({ resume_document: documentData }) };
    };
    harness.load('resume.js');
    return { ...harness, form, submit };
}

const resumeFixture = {
    full_name: 'Test Learner', target_role: 'Backend engineer',
    contacts: [{ text: 'GitHub', href: 'https://github.com/example/my project' }],
    blocks: [{ kind: 'heading', spans: [{ text: 'Projects' }] },
        { kind: 'bullet', spans: [{ text: '<img src=x onerror=alert(1)>', bold: true }, { text: 'Source', href: 'https://github.com/example/repo' }] }],
};

test('resume renders structured sections safely without CDN libraries', async () => {
    const harness = resumeBrowser(resumeFixture);
    await harness.document.emit('DOMContentLoaded');
    await harness.form.emit('submit');
    const output = harness.document.getElementById('resume-output');
    assert.equal(output.innerHTML, '');
    assert.ok(output.textContent.includes('<img src=x onerror=alert(1)>'));
    assert.equal(output.children[0].children[0].tagName, 'h1');
    assert.equal(output.children[1].tagName, 'h2');
    assert.equal(output.children[2].tagName, 'ul');
    assert.equal(output.classList.contains('hidden'), false);
    const link = output.children[0].children[2].children[0].children[0];
    assert.equal(link.href, 'https://github.com/example/my%20project');
    assert.equal(link.rel, 'noopener noreferrer');
    assert.equal(harness.submit.disabled, false);
});

for (const href of ['javascript:alert(1)', '//evil.example', 'data:text/html,evil', 'https://user:password@example.com', 'https://example.com\n/evil']) {
    test(`resume does not activate unsafe link: ${JSON.stringify(href)}`, async () => {
        const harness = resumeBrowser({ ...resumeFixture, contacts: [{ text: 'Profile', href }] });
        await harness.document.emit('DOMContentLoaded');
        await harness.form.emit('submit');
        const output = harness.document.getElementById('resume-output');
        assert.equal(output.children[0].children[2].children[0].children[0].tagName, 'span');
    });
}

test('resume export requests a real PDF without making another AI call', async () => {
    const harness = resumeBrowser(resumeFixture);
    await harness.document.emit('DOMContentLoaded');
    await harness.form.emit('submit');
    const events = [];
    harness.document.body = harness.document.createElement('body');
    const create = harness.document.createElement;
    harness.document.createElement = tag => {
        const element = create(tag);
        element.click = () => events.push(['download', element.download]);
        return element;
    };
    harness.context.URL = class extends URL {
        static createObjectURL(blob) { assert.equal(blob.type, 'application/pdf'); return 'blob:fixture'; }
        static revokeObjectURL(value) { events.push(['revoke', value]); }
    };
    harness.context.setTimeout = callback => callback();
    harness.context.authFetch = async (url, options) => {
        assert.equal(url, '/resume/export');
        assert.equal(options.body.full_name, 'Test Learner');
        return { ok: true, headers: { get: () => 'application/pdf' }, blob: async () => new Blob(['%PDF-1.4'], { type: 'application/pdf' }) };
    };
    await harness.document.getElementById('download-resume').emit('click');
    assert.deepEqual(events, [['download', 'Test-Learner-Resume.pdf'], ['revoke', 'blob:fixture']]);
    assert.equal(harness.document.getElementById('download-resume').disabled, false);
});

test('resume export reports a failed PDF without downloading an error page', async () => {
    const harness = resumeBrowser(resumeFixture);
    await harness.document.emit('DOMContentLoaded');
    await harness.form.emit('submit');
    harness.context.authFetch = async () => ({ ok: true, headers: { get: () => 'text/html' } });
    await harness.document.getElementById('download-resume').emit('click');
    assert.ok(harness.document.getElementById('resume-status').textContent.includes('did not return a PDF'));
    assert.equal(harness.document.getElementById('download-resume').disabled, false);
});

test('resume rejects a missing document instead of displaying unformatted Markdown', async () => {
    const harness = resumeBrowser(null);
    harness.document.getElementById('download-resume').classList.add('hidden');
    await harness.document.emit('DOMContentLoaded');
    await harness.form.emit('submit');
    assert.ok(harness.document.getElementById('resume-status').textContent.includes('could not be formatted'));
    assert.equal(harness.document.getElementById('download-resume').classList.contains('hidden'), true);
});
