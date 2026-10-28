const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.argv[2] || 'playwright');
const base = process.argv[3] || 'http://127.0.0.1:8882';

async function main() {
    assert.ok(['127.0.0.1', 'localhost'].includes(new URL(base).hostname), 'Use only the isolated spoken interview fixture server');
    const launch = () => chromium.launch({ channel: 'msedge', headless: true, args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] });
    let browser = await launch();
    fs.mkdirSync('artifacts/spoken', { recursive: true });
    try {
        for (const width of [1440, 390]) {
            const context = await browser.newContext({ viewport: { width, height: 1000 } });
            await context.addInitScript(() => {
                localStorage.setItem('access_token', 'fixture-not-real');
                localStorage.setItem('user', JSON.stringify({ id: 'fixture-user', name: 'Alex Morgan', profile: { experience_level: 'fresher' } }));
                localStorage.setItem('theme', 'light');
                window.confirm = () => true;
            });
            const page = await context.newPage();
            await page.bringToFront();
            const errors = [];
            page.on('pageerror', error => errors.push(error.message));
            await page.goto(base + '/mock-interview', { waitUntil: 'networkidle' });
            await page.locator('.mi-domain-card').click();
            await page.locator('#spoken-open').click();
            await page.waitForLoadState('networkidle');
            await page.locator('#spoken-start').click();
            await page.waitForFunction(() => document.getElementById('spoken-status').textContent.includes('accept'));
            await page.locator('#spoken-consent').check();
            await page.locator('#spoken-count').selectOption('3');
            await page.locator('#spoken-role').fill('Inference engineer');
            await page.locator('#spoken-preview').click();
            await page.waitForFunction(() => !document.getElementById('spoken-preview').disabled);
            await page.screenshot({ path: `artifacts/spoken/setup-${width}.png`, fullPage: true });
            await page.locator('#spoken-start').click();
            await page.waitForSelector('#spoken-session:not(.hidden)');
            await page.waitForFunction(() => !document.getElementById('spoken-record').disabled);
            assert.equal(await page.locator('#spoken-video').evaluate(video => video.srcObject.getVideoTracks().length), 1);
            await page.screenshot({ path: `artifacts/spoken/room-${width}.png`, fullPage: true });
            let failedTranscription = false;
            await page.route(base + '/mock-interview/spoken/transcribe/**', async route => {
                if (!failedTranscription) { failedTranscription = true; return route.fulfill({ status: 503, json: { detail: 'Synthetic temporary transcription failure' } }); }
                return route.continue();
            });
            await page.locator('#spoken-record').click();
            await page.waitForFunction(() => !document.getElementById('spoken-stop').disabled, { timeout: 10000 }).catch(async error => {
                console.error(JSON.stringify({ width, status: await page.locator('#spoken-status').innerText(), hidden: await page.evaluate(() => document.hidden), errors }));
                throw error;
            });
            await page.waitForTimeout(1200);
            if (await page.locator('#spoken-stop').isDisabled()) {
                console.error(JSON.stringify({ width, recording_status: await page.locator('#spoken-status').innerText(), hidden: await page.evaluate(() => document.hidden), errors }));
                await page.screenshot({ path: `artifacts/spoken/recording-error-${width}.png`, fullPage: true });
            }
            await page.locator('#spoken-stop').click();
            await page.waitForSelector('#spoken-retry-transcript:not(.hidden)');
            assert.equal(await page.locator('#spoken-transcript').inputValue(), '');
            await page.locator('#spoken-retry-transcript').click();
            await page.waitForFunction(() => document.getElementById('spoken-transcript').value.includes('Leaf'));
            await page.locator('#spoken-submit').click();
            await page.waitForFunction(() => document.getElementById('spoken-question').textContent.includes('Leaf'));
            await page.waitForFunction(() => !document.getElementById('spoken-submit').disabled);
            const savedIdentifier = await page.evaluate(() => sessionStorage.getItem('spoken-interview:fixture-user'));
            await page.reload({ waitUntil: 'networkidle' });
            await page.locator('.mi-domain-card').click();
            await page.locator('#spoken-open').click();
            await page.locator('#spoken-consent').check();
            await page.locator('#spoken-saved').selectOption(savedIdentifier);
            await page.locator('#spoken-resume').click();
            await page.waitForFunction(() => document.getElementById('spoken-progress').textContent.includes('2 of 3'));
            await page.waitForFunction(() => !document.getElementById('spoken-submit').disabled);
            await page.locator('#spoken-transcript').fill('Leaf uses continuous batching. I measured p95 latency and throughput under load.');
            await page.locator('#spoken-submit').click();
            await page.waitForFunction(() => document.getElementById('spoken-progress').textContent.includes('3 of 3'));
            await page.waitForFunction(() => !document.getElementById('spoken-end').disabled);
            await page.locator('#spoken-end').click();
            await page.waitForSelector('#spoken-report:not(.hidden)');
            assert.equal(await page.locator('#spoken-video').evaluate(video => video.srcObject), null);
            assert.equal(await page.locator('.spoken-review-turn').count(), 2);
            assert.ok((await page.locator('#spoken-report').innerText()).includes('Leaf'));
            assert.ok((await page.locator('#spoken-report-limitations').innerText()).includes('eye contact'));
            assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
            await page.screenshot({ path: `artifacts/spoken/report-${width}.png`, fullPage: true });
            const deletedIdentifier = await page.evaluate(() => sessionStorage.getItem('spoken-interview:fixture-user'));
            await page.locator('#spoken-delete').click();
            await page.waitForFunction(() => document.getElementById('spoken-status').textContent.includes('deleted'));
            assert.equal((await context.request.get(base + '/mock-interview/spoken/session/' + deletedIdentifier)).status(), 404);
            assert.deepEqual(errors, []);
            console.log(JSON.stringify({ width, consent: true, synthetic_camera_and_mic: true, record_transcribe_retry: true, contextual_follow_up: true, report: true, deleted: true }));
            await context.close();
            await browser.close();
            browser = await launch();
        }
        const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
        await context.addInitScript(() => {
            localStorage.setItem('access_token', 'fixture-not-real');
            localStorage.setItem('user', JSON.stringify({ id: 'fixture-user', name: 'Alex Morgan' }));
            Object.defineProperty(navigator.mediaDevices, 'getUserMedia', { value: async () => { throw new DOMException('Synthetic denied permission', 'NotAllowedError'); } });
            window.confirm = () => true;
        });
        const page = await context.newPage();
        await page.route(base + '/mock-interview/spoken/speech', route => route.fulfill({ status: 503, json: { detail: 'Synthetic audio playback unavailable' } }));
        await page.goto(base + '/mock-interview');
        await page.locator('.mi-domain-card').click();
        await page.locator('#spoken-open').click();
        await page.locator('#spoken-consent').check();
        await page.locator('#spoken-count').selectOption('3');
        await page.locator('#spoken-start').click();
        await page.waitForSelector('#spoken-session:not(.hidden)');
        await page.waitForFunction(() => !document.getElementById('spoken-submit').disabled);
        assert.equal(await page.locator('#spoken-video').evaluate(video => video.srcObject), null);
        assert.ok((await page.locator('#spoken-status').innerText()).includes('Voice playback unavailable'));
        await page.locator('#spoken-transcript').fill('I built Leaf, an inference engine. I implemented its scheduler.');
        await page.locator('#spoken-submit').click();
        await page.waitForFunction(() => document.getElementById('spoken-progress').textContent.includes('2 of'));
        await page.waitForFunction(() => !document.getElementById('spoken-submit').disabled);
        await page.locator('#spoken-transcript').fill('Leaf uses continuous batching to share GPU work.');
        await page.locator('#spoken-submit').click();
        await page.waitForFunction(() => document.getElementById('spoken-progress').textContent.includes('3 of'));
        await page.waitForFunction(() => !document.getElementById('spoken-submit').disabled);
        await page.locator('#spoken-transcript').fill('I would evaluate Leaf with realistic request sizes and measure throughput and tail latency.');
        await page.locator('#spoken-submit').click();
        await page.waitForSelector('#spoken-report:not(.hidden)');
        assert.equal(await page.locator('.spoken-review-turn').count(), 3);
        await page.locator('#spoken-delete').click();
        await page.waitForFunction(() => document.getElementById('spoken-status').textContent.includes('deleted'));
        console.log(JSON.stringify({ denied_devices: true, tts_failure: true, typed_fallback: true, automatic_completion: true }));
        await context.close();
    } finally { await browser.close(); }
}
main().catch(error => { console.error(error.stack); process.exitCode = 1; });
