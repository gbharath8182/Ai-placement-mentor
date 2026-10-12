const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.argv[2] || 'playwright');
const baseURL = process.argv[3] || 'http://127.0.0.1:8881';

async function main() {
    assert.ok(['127.0.0.1', 'localhost'].includes(new URL(baseURL).hostname), 'Use the isolated local resume fixture server, never production');
    const browser = await chromium.launch({ channel: 'msedge', headless: true });
    const output = path.resolve('artifacts/resume');
    fs.mkdirSync(output, { recursive: true });
    try {
        for (const width of [1440, 390]) {
            const context = await browser.newContext({ viewport: { width, height: 1000 }, acceptDownloads: true });
            await context.addInitScript(() => {
                localStorage.setItem('access_token', 'fixture-not-a-real-access-token');
                localStorage.setItem('user', JSON.stringify({ name: 'Alex Morgan', profile: { experience_level: 'fresher' } }));
                localStorage.setItem('theme', 'light');
            });
            const page = await context.newPage();
            const errors = [];
            page.on('pageerror', error => errors.push(error.message));
            await page.route('https://cdnjs.cloudflare.com/**', route => route.abort());
            await page.route('https://cdn.jsdelivr.net/**', route => route.abort());
            await page.goto(baseURL + '/resume', { waitUntil: 'networkidle' });
            assert.equal(await page.locator('.workspace-profile #user-name').innerText(), 'Alex Morgan');
            await page.locator('[name="full_name"]').fill('Alex Morgan');
            await page.locator('[name="target_role"]').fill('Backend engineer');
            await page.locator('[name="email"]').fill('alex@example.com');
            await page.locator('[name="location"]').fill('Bengaluru, India');
            await page.locator('[name="github_url"]').fill('https://github.com/example');
            await page.locator('[name="linkedin_url"]').fill('https://www.linkedin.com/in/example');
            await page.locator('[name="portfolio_url"]').fill('https://example.com/my%20portfolio?language=Python&sort=new');
            await page.locator('[name="skills"]').fill('Python, JavaScript, SQL, FastAPI, MongoDB, Git, Docker, pytest');
            await page.locator('[name="education"]').fill('BSc Computer Science, Example University, 2026.');
            await page.locator('[name="achievements"]').fill('Presented the study planner at the university engineering showcase.');
            await page.locator('[data-project="title"]').fill('Study planner');
            await page.locator('[data-project="description"]').fill('Built a scheduling API with authenticated access and user-scoped study records. Added automated tests for validation and account isolation.');
            await page.locator('[data-project="technologies"]').fill('Python, FastAPI, MongoDB, pytest');
            await page.locator('[data-project="github_url"]').fill('https://github.com/example/study-planner');
            await page.locator('[data-project="live_url"]').fill('https://example.com/study%20planner');
            await page.locator('button[type="submit"]').click();
            await page.waitForSelector('#resume-output:not(.hidden)');
            assert.equal(await page.locator('#resume-output h1').innerText(), 'Alex Morgan');
            assert.ok(await page.locator('#resume-output h2').count() >= 4);
            assert.equal(await page.locator('#resume-output .resume-paper-contacts a').first().getAttribute('href'), 'mailto:alex@example.com');
            const github = page.locator('#resume-output .resume-paper-contacts a').filter({ hasText: /^GitHub$/ });
            assert.equal(await github.getAttribute('href'), 'https://github.com/example');
            assert.equal(await github.getAttribute('rel'), 'noopener noreferrer');
            for (const [label, destination] of [['GitHub', 'https://github.com/example'], ['LinkedIn', 'https://www.linkedin.com/in/example'], ['Portfolio', 'https://example.com/my%20portfolio?language=Python&sort=new']]) {
                await context.route(destination, route => route.fulfill({ status: 200, contentType: 'text/html', body: '<title>Offline link destination fixture</title>' }));
                const opened = page.waitForEvent('popup');
                await page.locator('#resume-output .resume-paper-contacts a').filter({ hasText: new RegExp(`^${label}$`) }).click();
                const popup = await opened;
                await popup.waitForLoadState('domcontentloaded');
                assert.equal(popup.url(), destination);
                await popup.close();
            }
            assert.ok((await page.locator('#resume-output').innerText()).includes('Study planner'));
            assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
            const downloadEvent = page.waitForEvent('download');
            await page.locator('#download-resume').click();
            const download = await downloadEvent;
            assert.equal(download.suggestedFilename(), 'Alex-Morgan-Resume.pdf');
            const filename = path.join(output, `resume-${width}.pdf`);
            await download.saveAs(filename);
            assert.equal(fs.readFileSync(filename).subarray(0, 5).toString(), '%PDF-');
            await page.locator('[name="github_url"]').fill(baseURL + '/resume');
            await page.locator('button[type="submit"]').click();
            await page.waitForFunction(() => document.getElementById('resume-status').textContent.includes('actual github.com'));
            assert.equal(await page.locator('#resume-output h1').innerText(), 'Alex Morgan');
            await page.evaluate(() => window.scrollTo(0, 0));
            await page.screenshot({ path: path.join(output, `studio-${width}.png`), fullPage: true });
            await page.locator('#resume-output').screenshot({ path: path.join(output, `paper-${width}.png`) });
            await page.evaluate(() => window.scrollTo(0, 0));
            if (width <= 960) await page.locator('.workspace-menu').click();
            await page.locator('#theme-toggle').click();
            if (width <= 960) await page.keyboard.press('Escape');
            assert.equal(await page.locator('#resume-output').evaluate(element => getComputedStyle(element).backgroundColor), 'rgb(255, 255, 255)');
            await page.screenshot({ path: path.join(output, `studio-dark-${width}.png`), fullPage: true });
            assert.deepEqual(errors, []);
            console.log(JSON.stringify({ width, preview: true, pdf_download: true, links: true, no_cdn: true, invalid_profile_rejected: true }));
            await context.close();
        }
    } finally { await browser.close(); }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
