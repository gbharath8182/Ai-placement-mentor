const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.argv[2] || 'playwright');
const baseURL = process.argv[3] || 'http://127.0.0.1:8883';
const output = path.resolve('artifacts/product');

async function main() {
    fs.mkdirSync(output, { recursive: true });
    const browser = await chromium.launch({ ...(process.env.CI ? {} : { channel: 'msedge' }), headless: true });
    try {
        for (const width of [1440, 390]) {
            for (const theme of ['dark', 'light']) {
                const context = await browser.newContext({ viewport: { width, height: 960 }, reducedMotion: 'reduce' });
                await context.addInitScript(theme => {
                    localStorage.setItem('theme', theme);
                    localStorage.setItem('access_token', 'fixture-not-a-real-token');
                    localStorage.setItem('user', JSON.stringify({ id: '000000000000000000000001', name: 'Alex Morgan', profile: { experience_level: 'fresher' } }));
                }, theme);
                const page = await context.newPage();
                const errors = [];
                page.on('pageerror', error => errors.push(error.message));
                await page.goto(baseURL, { waitUntil: 'networkidle' });
                await page.locator('#tab-interview').click();
                assert.equal(await page.locator('#example-interview').isVisible(), true);
                await page.keyboard.press('ArrowRight');
                assert.equal(await page.locator('#example-resume').isVisible(), true);
                await page.keyboard.press('Home');
                assert.equal(await page.locator('#example-study').isVisible(), true);
                assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
                await page.screenshot({ path: path.join(output, `home-${theme}-${width}.png`), fullPage: true });
                await page.goto(`${baseURL}/dashboard`, { waitUntil: 'networkidle' });
                await page.waitForSelector('#study-overview[aria-busy="false"]');
                assert.match(await page.locator('#study-main').innerText(), /Continue lesson/);
                assert.equal(await page.locator('#review-count').innerText(), '1');
                assert.equal(await page.locator('#stats-streak').innerText(), '3 days');
                assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
                await page.screenshot({ path: path.join(output, `dashboard-${theme}-${width}.png`), fullPage: true });
                await page.locator('.workspace-search-trigger').click();
                await page.locator('#command-input').fill('values');
                await page.waitForFunction(() => document.querySelector('.command-status').textContent.includes('result'));
                assert.ok(await page.locator('.command-results a[href*="/topic/"]').count() > 0);
                await page.keyboard.press('ArrowDown');
                assert.equal(await page.evaluate(() => document.activeElement.className), 'command-result');
                await page.screenshot({ path: path.join(output, `search-${theme}-${width}.png`) });
                await page.keyboard.press('Escape');
                assert.equal(await page.locator('.workspace-search-trigger').evaluate(node => node === document.activeElement), true);
                await page.keyboard.press('Control+k');
                await page.locator('#command-input').fill('resume');
                await page.keyboard.press('Enter');
                await page.waitForURL('**/resume');
                assert.deepEqual(errors, []);
                console.log(JSON.stringify({ width, theme, homepage: true, dashboard: true, search: true, keyboard: true, noOverflow: true }));
                await context.close();
            }
        }
        const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
        await context.addInitScript(() => {
            localStorage.setItem('access_token', 'fixture-not-a-real-token');
            localStorage.setItem('user', JSON.stringify({ id: '000000000000000000000001', name: 'Alex Morgan' }));
        });
        const page = await context.newPage();
        let failOverview = true;
        await page.route('**/workspace/overview', route => failOverview ? route.fulfill({ status: 503, json: { detail: 'Unavailable' } }) : route.continue());
        await page.goto(`${baseURL}/dashboard`, { waitUntil: 'networkidle' });
        assert.equal(await page.getByRole('button', { name: 'Retry study queue' }).isVisible(), true);
        assert.equal(await page.locator('#stats-mastered').innerText(), '—');
        failOverview = false;
        await page.getByRole('button', { name: 'Retry study queue' }).click();
        await page.waitForFunction(() => document.querySelector('#review-count').textContent === '1');
        await page.route('**/catalog/search?*', route => route.fulfill({ status: 503, json: { detail: 'Unavailable' } }));
        await page.locator('.workspace-search-trigger').click();
        await page.locator('#command-input').fill('resume');
        await page.waitForFunction(() => document.querySelector('.command-status').textContent.includes('unavailable'));
        assert.equal(await page.locator('.command-results a[href="/resume"]').count(), 1);
        await page.keyboard.press('Escape');
        await context.setOffline(true);
        assert.equal(await page.locator('.workspace-connection').isVisible(), true);
        await context.setOffline(false);
        await page.waitForFunction(() => document.querySelector('.workspace-connection').hidden);
        await page.unroute('**/catalog/search?*');
        await page.route('**/catalog/search?*', async route => {
            const query = new URL(route.request().url()).searchParams.get('q');
            if (query === 'older') await new Promise(resolve => setTimeout(resolve, 700));
            await route.fulfill({ json: { results: [{ slug: query === 'older' ? 'older' : 'fresh', title: query === 'older' ? 'Stale result' : '<img src=x onerror=alert(1)>', domain_slug: 'python', difficulty: 'beginner' }], degraded: false } }).catch(() => {});
        });
        await page.locator('.workspace-search-trigger').click();
        await page.locator('#command-input').fill('older');
        await page.waitForTimeout(300);
        await page.locator('#command-input').fill('fresh');
        await page.waitForFunction(() => document.querySelector('.command-results a[href="/topic/fresh"]'));
        await page.waitForTimeout(800);
        assert.equal(await page.locator('.command-results a[href="/topic/older"]').count(), 0);
        assert.equal(await page.locator('.command-results img').count(), 0);
        await page.keyboard.press('Escape');
        await page.unroute('**/workspace/overview');
        await page.route('**/workspace/overview', route => route.fulfill({ json: { continue: [], reviews: [], suggested: { slug: 'python-foundations-values-and-types', title: 'Values & types' }, counts: { review: 0, mastered: 0, in_progress: 0 }, limited: false, has_history: false, unavailable_lessons: 0, capabilities: { ai_configured: false, runner_configured: false } } }));
        await page.reload({ waitUntil: 'networkidle' });
        assert.match(await page.locator('#study-main').innerText(), /Your first study session/i);
        assert.match(await page.locator('#runner-note').innerText(), /not configured/);
        assert.match(await page.locator('#study-note').innerText(), /AI tools are not configured/);
        console.log(JSON.stringify({ failuresRecoverable: true, offlineNotice: true, staleSearchIgnored: true, injectionSafe: true, honestEmptyState: true }));
        await context.close();
    } finally { await browser.close(); }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
