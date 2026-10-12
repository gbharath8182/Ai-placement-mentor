const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const modulePath = process.argv[2] || 'playwright';
const baseURL = process.argv[3] || 'http://127.0.0.1:8879';
const { chromium } = require(modulePath);

async function main() {
    const browser = await chromium.launch({ channel: 'msedge', headless: true });
    const output = path.resolve('artifacts/browser');
    fs.mkdirSync(output, { recursive: true });
    let failures = 0;
    try {
        for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
            const context = await browser.newContext({ viewport, reducedMotion: 'reduce' });
            const page = await context.newPage();
            const pageErrors = [];
            page.on('pageerror', error => pageErrors.push(error.message));
            for (const route of ['/', '/learn', '/topic/python-foundations-values-and-types', '/login', '/signup', '/forgot-password', '/cheatsheets']) {
                try {
                    if (route === '/cheatsheets') {
                        await page.evaluate(() => {
                            localStorage.setItem('access_token', 'browser-smoke-only-not-a-real-token');
                            localStorage.setItem('user', JSON.stringify({ name: 'Test Reader', profile: { experience_level: 'fresher' } }));
                        });
                    }
                    const response = await page.goto(baseURL + route, { waitUntil: 'networkidle', timeout: 30000 });
                    assert.equal(response.status(), 200);
                    if (route.startsWith('/topic/')) {
                        await page.waitForFunction(() => document.getElementById('topic-title')?.textContent === 'Values, Types, and Name Binding');
                        assert.ok(await page.locator('#content-blocks-area').innerText());
                        if (viewport.width < 900) {
                            const toggle = page.locator('#ai-panel-toggle');
                            assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
                            await toggle.click();
                            assert.equal(await toggle.getAttribute('aria-expanded'), 'true');
                            await toggle.click();
                        }
                    }
                    if (route === '/cheatsheets') {
                        await page.locator('[data-target="books"]').click();
                        assert.equal(await page.locator('#panel-books .book-btn').count(), 12);
                        assert.equal(await page.locator('#panel-books').isVisible(), true);
                        assert.equal(await page.locator('#panel-books a[href*="mheducation.com"], #panel-books a[href*="dataintensive.net"]').count(), 0);
                    }
                    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
                    assert.equal(overflow, false, 'Horizontal page overflow');
                    assert.equal(pageErrors.length, 0, 'Unexpected JavaScript exception');
                    const name = route === '/' ? 'home' : route.startsWith('/topic/') ? 'lesson' : route.slice(1);
                    await page.screenshot({ path: path.join(output, `${name}-${viewport.width}.png`), fullPage: true });
                    if (route === '/') {
                        await page.locator('#theme-toggle').click();
                        assert.equal(await page.locator('html').evaluate(element => element.classList.contains('light-theme')), true);
                        await page.screenshot({ path: path.join(output, `home-light-${viewport.width}.png`), fullPage: true });
                        await page.locator('#theme-toggle').click();
                    }
                    console.log(JSON.stringify({ route, width: viewport.width, passed: true }));
                } catch (error) {
                    failures++;
                    console.log(JSON.stringify({ route, width: viewport.width, passed: false, reason: error.message, errors: pageErrors }));
                }
            }
            await context.close();
        }
    } finally { await browser.close(); }
    assert.equal(failures, 0, `${failures} browser checks failed`);
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
