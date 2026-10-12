const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { chromium } = require(process.argv[2] || 'playwright');
const baseURL = process.argv[3] || 'http://127.0.0.1:8879';
const domains = [
    { id: 'test-python', slug: 'python', title: 'Python programming', description: 'Build a clear mental model of the language and use it to solve practical problems.', topics: ['python-intro'] },
    { id: 'test-dsa', slug: 'dsa', title: 'Data structures & algorithms', description: 'Understand the trade-offs behind useful structures and develop reliable problem-solving techniques.', topics: ['dsa-intro'] },
    { id: 'test-sde', slug: 'sde', title: 'Software engineering', description: 'Connect programming fundamentals with design, testing and engineering judgment.', topics: ['sde-intro'] },
    { id: 'test-ml', slug: 'ml', title: 'Machine learning', description: 'Study models, evaluation and the reasoning behind effective learning systems.', topics: ['ml-intro'] },
    { id: 'test-systems', slug: 'system-design', title: 'System design', description: 'Reason about scalability, data and the boundaries between services.', topics: ['systems-intro'] },
    { id: 'test-web', slug: 'web-dev', title: 'Web development', description: 'Build accessible interfaces and understand the protocols that connect them.', topics: ['web-intro'] },
];

async function mockAPIs(page) {
    await page.route(baseURL + '/**', async route => {
        const request = route.request();
        const pathname = new URL(request.url()).pathname;
        if (request.resourceType() === 'document' || pathname.startsWith('/static/')) return route.continue();
        let payload = [];
        if (pathname === '/domains' || pathname === '/domains/with-details') payload = domains;
        else if (/\/domains\/[^/]+\/topics$/.test(pathname)) payload = [{ id: 'test-lesson', slug: 'python-intro', domain_slug: 'python', title: 'Values and types', difficulty: 'beginner', subtopics: [] }];
        else if (pathname.startsWith('/topics/')) return route.continue();
        else if (pathname === '/curriculum') return route.continue();
        else if (pathname.startsWith('/domains/') && pathname.endsWith('/details')) return route.fulfill({ status: 404, json: { detail: 'No detailed roadmap' } });
        else if (pathname.endsWith('/mastery')) payload = { status: 'not_assessed', reasons: ['Answer lesson checks to assess your understanding.'] };
        else if (pathname.startsWith('/ai/history/')) payload = { messages: [] };
        else if (pathname === '/activity/streak') payload = { current_streak: 2, longest_streak: 4 };
        else if (pathname === '/analytics/overview') payload = { total_minutes: 125, domains_active: 2, problems_solved: 1, consistency_pct: 65 };
        else if (pathname === '/analytics/domain-time') payload = { data: [], series: [] };
        else if (pathname === '/analytics/skill-coverage') payload = [{ domain: 'Python', completed: 1, total: 15, coverage: 7 }];
        else if (pathname.startsWith('/auth/')) payload = { detail: 'No real authentication in browser fixtures' };
        return route.fulfill({ status: 200, json: payload });
    });
}

async function main() {
    const browser = await chromium.launch({ channel: 'msedge', headless: true });
    const output = path.resolve('artifacts/workspace');
    fs.mkdirSync(output, { recursive: true });
    let failures = 0;
    try {
        for (const width of [1440, 390]) {
            const context = await browser.newContext({ viewport: { width, height: 960 }, reducedMotion: 'reduce' });
            await context.addInitScript(() => {
                localStorage.setItem('access_token', 'fixture-not-a-real-access-token');
                localStorage.setItem('user', JSON.stringify({ id: '000000000000000000000001', name: 'Alex Morgan', email: 'reader@example.com', profile: { experience_level: 'fresher', interests: [] } }));
                localStorage.setItem('theme', 'light');
            });
            const page = await context.newPage();
            await mockAPIs(page);
            let errors = [];
            page.on('pageerror', error => errors.push(error.message));
            for (const route of ['/dashboard', '/roadmap', '/analytics', '/profile', '/playground', '/mock-interview', '/resume', '/aptitude', '/cheatsheets', '/topic/python-foundations-values-and-types', '/learn']) {
                errors = [];
                try {
                    await page.goto(baseURL + route, { waitUntil: 'networkidle', timeout: 30000 });
                    await page.waitForSelector('.workspace-sidebar');
                    assert.equal(new URL(page.url()).pathname, route);
                    assert.equal(await page.locator('.workspace-sidebar').count(), 1);
                    assert.equal(await page.locator('.dashboard-nav').count(), 0);
                    assert.equal(await page.locator('.workspace-sidebar svg').count(), 0);
                    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false, 'horizontal overflow');
                    if (width > 960) {
                        const sidebar = await page.locator('.workspace-sidebar').boundingBox();
                        assert.equal(sidebar.x, 0);
                        assert.equal(sidebar.width, 238);
                    } else {
                        assert.equal(await page.locator('.workspace-sidebar').getAttribute('aria-hidden'), 'true');
                        await page.locator('.workspace-menu').click();
                        assert.equal(await page.locator('.workspace-menu').getAttribute('aria-expanded'), 'true');
                        await page.keyboard.press('Escape');
                        assert.equal(await page.locator('.workspace-menu').getAttribute('aria-expanded'), 'false');
                        assert.equal(await page.locator('.workspace-menu').evaluate(element => element === document.activeElement), true);
                    }
                    if (route === '/dashboard') {
                        assert.equal(await page.locator('.domain-card').count(), 6);
                        assert.equal(await page.locator('.domain-card svg').count(), 0);
                        await page.locator('#domain-search').fill('Python');
                        assert.equal(await page.locator('.domain-card').count(), 1);
                        await page.locator('.domain-card').click();
                        await page.waitForSelector('#topic-list a');
                        assert.equal(await page.locator('#topic-list a').getAttribute('href'), '/topic/python-intro');
                        await page.locator('#close-drawer-btn').click();
                        await page.locator('#domain-search').fill('');
                        assert.equal(await page.locator('#stats-streak').innerText(), '2 days');
                        if (width <= 960) await page.locator('.workspace-menu').click();
                        await page.locator('#theme-toggle').click();
                        assert.equal(await page.locator('html').evaluate(element => element.classList.contains('light-theme')), false);
                        await page.screenshot({ path: path.join(output, `dashboard-dark-${width}.png`), fullPage: true });
                        await page.locator('#theme-toggle').click();
                        if (width <= 960) await page.keyboard.press('Escape');
                    }
                    if (route === '/cheatsheets') await page.locator('[data-target="books"]').click();
                    assert.deepEqual(errors, [], 'JavaScript errors');
                    await page.screenshot({ path: path.join(output, `${route.includes('/topic/') ? 'lesson' : route.slice(1)}-${width}.png`), fullPage: true });
                    console.log(JSON.stringify({ route, width, passed: true }));
                } catch (error) {
                    failures++;
                    console.log(JSON.stringify({ route, width, passed: false, reason: error.message, errors }));
                }
            }
            await context.close();
            const anonymous = await browser.newContext({ viewport: { width, height: 960 }, reducedMotion: 'reduce' });
            const authPage = await anonymous.newPage();
            for (const route of ['/login', '/signup', '/forgot-password', '/reset-password']) {
                try {
                    await authPage.goto(baseURL + route, { waitUntil: 'networkidle' });
                    assert.equal(await authPage.locator('.auth-layout').count(), 1);
                    assert.equal(await authPage.locator('.auth-card svg').count(), 0);
                    assert.equal(await authPage.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
                    await authPage.screenshot({ path: path.join(output, `${route.slice(1)}-${width}.png`), fullPage: true });
                    console.log(JSON.stringify({ route, width, passed: true }));
                } catch (error) {
                    failures++;
                    console.log(JSON.stringify({ route, width, passed: false, reason: error.message }));
                }
            }
            await anonymous.close();
        }
    } finally { await browser.close(); }
    assert.equal(failures, 0, `${failures} workspace checks failed`);
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
