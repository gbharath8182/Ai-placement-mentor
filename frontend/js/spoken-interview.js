document.addEventListener('DOMContentLoaded', () => {
    const element = id => document.getElementById('spoken-' + id);
    if (!element('open')) return;
    const api = '/mock-interview/spoken';
    let session = null;
    let stream = null;
    let recorder = null;
    let audio = null;
    let audioURL = null;
    let questionAudio = null;
    let recordingBlob = null;
    let duration = 0;
    let timer = null;
    let recordingStarted = 0;
    let busy = false;
    let generation = 0;
    let requestController = new AbortController();
    const account = getUser();
    const storageKey = 'spoken-interview:' + (account?.id || account?.email || 'current-user');
    const status = text => { element('status').textContent = text; };
    const show = (id, visible) => element(id).classList.toggle('hidden', !visible);
    const textNode = (tag, text, className = '') => { const node = document.createElement(tag); node.textContent = text; node.className = className; return node; };

    async function loadSavedSessions() {
        const recent = await (await call('/sessions')).json();
        const saved = sessionStorage.getItem(storageKey);
        element('saved').replaceChildren(textNode('option', 'Select a saved session'));
        element('saved').firstChild.value = '';
        recent.forEach(item => {
            const option = textNode('option', `${item.domain} · ${item.status} · ${new Date(item.created_at).toLocaleDateString()}`);
            option.value = item.session_id;
            element('saved').appendChild(option);
        });
        if (recent.some(item => item.session_id === saved)) element('saved').value = saved;
        show('resume', recent.length > 0); show('delete-saved', recent.length > 0);
    }

    async function call(path, body, options = {}) {
        const response = await authFetch(api + path, { method: body === undefined ? 'GET' : 'POST', body, signal: requestController.signal, ...options });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(typeof data.detail === 'string' ? data.detail : 'The interview request failed. Your answer has not been discarded. Retry or resume the saved session.');
        }
        return response;
    }

    function refreshButtons() {
        const recording = recorder?.state === 'recording';
        element('record').disabled = busy || recording || !session || session.status !== 'active';
        element('stop').disabled = !recording;
        element('submit').disabled = busy || recording || !session || session.status !== 'active';
        element('replay').disabled = busy || recording;
        element('end').disabled = busy;
        element('start').disabled = busy;
        element('resume').disabled = busy;
        element('preview').disabled = busy;
    }

    function stopPlayback() {
        if (audio) { audio.pause(); audio.src = ''; audio = null; }
        if (audioURL) { URL.revokeObjectURL(audioURL); audioURL = null; }
    }

    function stopDevices() {
        if (timer) clearInterval(timer);
        timer = null;
        if (recorder?.state === 'recording') { recorder.onstop = null; recorder.stop(); }
        recorder = null;
        if (stream) stream.getTracks().forEach(track => track.stop());
        stream = null;
        element('video').srcObject = null;
        show('camera-placeholder', true);
        element('timer').textContent = 'Not recording';
        stopPlayback();
        refreshButtons();
    }

    function cancelWork() {
        generation += 1;
        requestController.abort();
        requestController = new AbortController();
        busy = false;
        stopDevices();
    }

    async function connectDevices() {
        if (!element('consent').checked) { status('Read and accept the audio/transcript notice before enabling devices.'); return; }
        const current = generation;
        if (!navigator.mediaDevices?.getUserMedia || !window.isSecureContext) { status('Camera and microphone need HTTPS or localhost. You can still type your answers.'); return; }
        stopDevices();
        try {
            const media = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true }, video: element('camera').checked ? { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } } : false });
            if (current !== generation) { media.getTracks().forEach(track => track.stop()); return; }
            stream = media;
            element('video').srcObject = stream;
            show('camera-placeholder', stream.getVideoTracks().length === 0);
            element('camera-toggle').textContent = stream.getVideoTracks().length ? 'Turn camera off' : 'Turn camera on';
            status('Devices ready. Camera stays local. Record when you are ready.');
            stream.getTracks().forEach(track => track.addEventListener('ended', () => { if (stream === media) { stopDevices(); status('A device disconnected. Reconnect devices or type your answer.'); } }));
        } catch (error) { status('Camera or microphone permission was not granted. You can reconnect with camera disabled, or type your answers.'); }
    }

    async function playBlob(blob, current) {
        if (current !== generation) return;
        stopPlayback();
        audioURL = URL.createObjectURL(blob);
        audio = new Audio(audioURL);
        audio.onended = () => { if (current === generation) status('Your turn. Take a breath, then record your answer.'); };
        await audio.play();
    }

    async function speakQuestion() {
        if (!session || busy || recorder?.state === 'recording') return;
        const current = generation;
        busy = true;
        refreshButtons();
        status('Preparing the interviewer’s voice…');
        try {
            if (!questionAudio) {
                const response = await call('/speech', { session_id: session.session_id, question_number: session.question_number });
                if (!response.headers.get('content-type')?.includes('audio/')) throw new Error('The service did not return playable audio.');
                questionAudio = await response.blob();
            }
            await playBlob(questionAudio, current);
            if (current === generation) status('Interviewer speaking. Press Record answer when you are ready to take your turn.');
        } catch (error) { if (current === generation) status('Voice playback unavailable: ' + error.message + ' The question text is still available; replay or continue.'); }
        finally { if (current === generation) { busy = false; refreshButtons(); } }
    }

    function renderQuestion(data) {
        session = data;
        sessionStorage.setItem(storageKey, data.session_id);
        questionAudio = null;
        recordingBlob = null;
        duration = 0;
        element('transcript').value = '';
        element('question').textContent = data.question;
        element('progress').textContent = `Question ${data.question_number} of ${data.total_questions}`;
        element('interviewer-label').textContent = `${data.voice[0].toUpperCase() + data.voice.slice(1)} / AI interviewer`;
        element('timer').textContent = 'Not recording';
        show('setup', false); show('session', true); show('report', false); show('retry-transcript', false);
        refreshButtons();
        element('question').focus();
    }

    async function transcribeRecording() {
        if (!recordingBlob || !session || busy) return;
        const current = generation;
        busy = true; refreshButtons();
        show('retry-transcript', false);
        status('Transcribing your answer. Nothing is submitted until you confirm it.');
        try {
            const response = await call(`/transcribe/${encodeURIComponent(session.session_id)}/${session.question_number}`, recordingBlob, { headers: { 'Content-Type': recordingBlob.type } });
            const data = await response.json();
            if (current !== generation) return;
            element('transcript').value = data.transcript;
            recordingBlob = null;
            status('Transcript ready. Correct names and technical terms, then send your answer.');
            element('transcript').focus();
        } catch (error) { if (current === generation) { show('retry-transcript', true); status(error.message + ' Retry transcription without re-recording, or type the answer.'); } }
        finally { if (current === generation) { busy = false; refreshButtons(); } }
    }

    async function record() {
        if (busy || !session) return;
        if (element('transcript').value.trim() && !window.confirm('Replace this unsent answer with a new recording?')) return;
        if (!stream?.getAudioTracks().some(track => track.readyState === 'live')) await connectDevices();
        if (!stream?.getAudioTracks().some(track => track.readyState === 'live')) return;
        if (typeof MediaRecorder === 'undefined') { status('This browser cannot record audio. Type an answer or use a current Chrome, Edge, Firefox or Safari browser.'); return; }
        stopPlayback();
        const mimeType = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus', 'audio/webm'].find(type => MediaRecorder.isTypeSupported(type));
        if (!mimeType) { status('No supported audio recording format. Type your answer instead.'); return; }
        const chunks = [];
        let size = 0;
        let tooLarge = false;
        const current = generation;
        try {
            recorder = new MediaRecorder(new MediaStream(stream.getAudioTracks()), { mimeType, audioBitsPerSecond: 64000 });
            recorder.ondataavailable = event => {
                size += event.data.size;
                if (size > 8 * 1024 * 1024) { tooLarge = true; if (recorder?.state === 'recording') recorder.stop(); }
                else chunks.push(event.data);
            };
            recorder.onerror = () => { stopDevices(); status('Recording failed. Reconnect devices or type your answer.'); };
            recorder.onstop = async () => {
                if (timer) clearInterval(timer);
                timer = null;
                duration = Math.min(180, (performance.now() - recordingStarted) / 1000);
                recorder = null;
                if (current !== generation) return;
                if (tooLarge) { status('Recording exceeded 8 MB. Please record a shorter answer.'); refreshButtons(); return; }
                recordingBlob = new Blob(chunks, { type: mimeType });
                element('timer').textContent = `${Math.round(duration)} seconds recorded`;
                refreshButtons();
                await transcribeRecording();
            };
            recordingStarted = performance.now();
            duration = 0;
            recordingBlob = null;
            recorder.start(1000);
            timer = setInterval(() => {
                const seconds = Math.floor((performance.now() - recordingStarted) / 1000);
                element('timer').textContent = `Recording ${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')} / 3:00`;
                if (seconds >= 180 && recorder?.state === 'recording') recorder.stop();
            }, 250);
            status('Recording audio only. Press Stop & transcribe when you finish.');
            refreshButtons();
        } catch { stopDevices(); status('Could not start recording. Reconnect devices or type your answer.'); }
    }

    function renderReport(report) {
        stopDevices();
        show('session', false); show('setup', false); show('report', true);
        element('report-limitations').textContent = report.limitations;
        element('scores').replaceChildren();
        const labels = { clarity: 'Clarity', relevance: 'Relevance', specificity: 'Specific evidence', technical_reasoning: 'Reasoning' };
        Object.entries(labels).forEach(([key, label]) => {
            const box = textNode('div', '', 'spoken-score');
            box.append(textNode('strong', report.scores[key] === null ? 'Not assessed' : `${report.scores[key]}/10`), textNode('span', label));
            element('scores').appendChild(box);
        });
        element('review-turns').replaceChildren();
        report.turns.forEach((turn, index) => {
            const section = textNode('section', '', 'spoken-review-turn');
            section.append(textNode('h3', `${index + 1}. ${turn.question}`), textNode('blockquote', turn.answer));
            if (turn.review.context_quote) section.appendChild(textNode('p', 'Context carried forward: “' + turn.review.context_quote + '”'));
            for (const [field, label] of [['strengths', 'Build on'], ['improvements', 'Improve next']]) {
                section.appendChild(textNode('h4', label));
                const list = document.createElement('ul');
                turn.review[field].forEach(text => list.appendChild(textNode('li', text)));
                section.appendChild(list);
            }
            section.appendChild(textNode('p', 'Practice: ' + turn.review.practice));
            const metrics = turn.metrics;
            section.appendChild(textNode('p', `${metrics.words} words · ${metrics.filler_phrases} filler phrases detected` + (metrics.estimated_words_per_minute === null ? '' : ` · approximately ${metrics.estimated_words_per_minute} words/minute (recording-time estimate)`), 'spoken-small'));
            section.appendChild(textNode('p', metrics.note, 'spoken-small'));
            element('review-turns').appendChild(section);
        });
        status(report.answered ? 'Session complete. Review the evidence and choose one thing to practice next.' : 'Session ended without a submitted answer. No scores were fabricated.');
        element('report').setAttribute('tabindex', '-1');
        element('report').focus();
    }

    element('open').addEventListener('click', async () => {
        miEl('mi-domain-select').classList.add('hidden');
        show('studio', true); show('setup', true); show('session', false); show('report', false);
        const saved = sessionStorage.getItem(storageKey);
        show('resume', Boolean(saved)); show('delete-saved', Boolean(saved));
        status('Choose a voice, review the privacy notice and start when ready.');
        try {
            const data = await (await call('/capabilities')).json();
            if (!data.configured) status('Spoken interviews are not configured on this server yet. Ask the administrator to enable Groq audio access.');
            await loadSavedSessions();
        } catch (error) { status(error.message); }
    });

    element('preview').addEventListener('click', async () => {
        if (busy) return;
        const current = generation;
        busy = true; refreshButtons(); status('Loading the voice sample…');
        try { const response = await call('/preview-voice', { voice: element('voice').value }); await playBlob(await response.blob(), current); if (current === generation) status('Voice sample playing. Choose the voice you prefer.'); }
        catch (error) { if (current === generation) status('Voice sample unavailable: ' + error.message); }
        finally { if (current === generation) { busy = false; refreshButtons(); } }
    });

    element('start').addEventListener('click', async () => {
        if (busy) return;
        if (!element('consent').checked) { status('Please accept the audio/transcript notice before starting.'); return; }
        cancelWork();
        const current = generation;
        busy = true; refreshButtons(); status('Starting your session…');
        try {
            const data = await (await call('/start', { domain_slug: miState.domainSlug, target_role: element('role').value.trim(), num_questions: Number(element('count').value), voice: element('voice').value, consent: true })).json();
            if (current !== generation) return;
            renderQuestion(data);
            await connectDevices();
            busy = false; refreshButtons(); await speakQuestion();
        } catch (error) { if (current === generation) status(error.message); }
        finally { if (current === generation) { busy = false; refreshButtons(); } }
    });

    element('resume').addEventListener('click', async () => {
        if (!element('consent').checked) { status('Accept the notice to resume this session.'); return; }
        if (busy) return;
        const current = generation;
        busy = true; refreshButtons();
        try {
            const id = element('saved').value || sessionStorage.getItem(storageKey);
            if (!id) throw new Error('Select a saved session first.');
            const data = await (await call('/session/' + encodeURIComponent(id))).json();
            if (current !== generation) return;
            session = data;
            sessionStorage.setItem(storageKey, data.session_id);
            if (data.status !== 'active') renderReport(data.summary);
            else { renderQuestion(data); await connectDevices(); }
        } catch (error) { if (current === generation) status(error.message + ' You may delete the saved session and start again.'); }
        finally { if (current === generation) { busy = false; refreshButtons(); } }
    });

    element('submit').addEventListener('click', async () => {
        if (busy || !session || recorder?.state === 'recording') return;
        const answer = element('transcript').value.trim();
        if (!answer) { status('Record or type an answer before sending.'); return; }
        stopPlayback();
        const current = generation;
        busy = true; refreshButtons(); status('Listening to your answer and preparing a relevant follow-up…');
        try {
            const data = await (await call('/answer', { session_id: session.session_id, question_number: session.question_number, answer, duration_seconds: duration, delivery: duration > 0 ? 'spoken' : 'typed' })).json();
            if (current !== generation) return;
            session = data;
            if (data.done) renderReport(data.summary);
            else { renderQuestion(data); busy = false; refreshButtons(); await speakQuestion(); }
        } catch (error) { if (current === generation) status(error.message + ' Your text is still here. If the response was lost, use Back then Resume saved session before resubmitting.'); }
        finally { if (current === generation) { busy = false; refreshButtons(); } }
    });

    element('end').addEventListener('click', async () => {
        if (busy || !session) return;
        if (element('transcript').value.trim() && !window.confirm('End without submitting this unsent answer?')) return;
        cancelWork(); busy = true; refreshButtons(); status('Devices stopped. Preparing your session review…');
        try { const data = await (await call('/end', { session_id: session.session_id })).json(); session.status = 'ended'; recordingBlob = null; renderReport(data.summary); }
        catch (error) { status(error.message + ' Your devices are off. Resume the session to retry ending it.'); }
        finally { busy = false; refreshButtons(); }
    });

    async function deleteSaved() {
        const inReport = !element('report').classList.contains('hidden');
        const id = inReport ? session?.session_id : element('saved').value || sessionStorage.getItem(storageKey);
        if (!id || busy || !window.confirm('Permanently delete the saved transcript and feedback for this session?')) return;
        cancelWork(); busy = true; refreshButtons();
        try {
            await call('/session/' + encodeURIComponent(id), undefined, { method: 'DELETE' });
            sessionStorage.removeItem(storageKey); session = null; recordingBlob = null; element('transcript').value = '';
            show('report', false); show('session', false); show('setup', true); show('resume', false); show('delete-saved', false);
            status('Session transcript and feedback deleted.');
            await loadSavedSessions();
        } catch (error) { status(error.message); }
        finally { busy = false; refreshButtons(); }
    }

    element('back').addEventListener('click', () => { cancelWork(); recordingBlob = null; show('studio', false); miShowPanel('mi-domain-select'); miPageShowModeStep(); });
    element('again').addEventListener('click', async () => { cancelWork(); show('report', false); show('setup', true); try { await loadSavedSessions(); } catch (error) { status(error.message); } });
    element('delete').addEventListener('click', deleteSaved);
    element('delete-saved').addEventListener('click', deleteSaved);
    element('record').addEventListener('click', record);
    element('stop').addEventListener('click', () => { if (recorder?.state === 'recording') recorder.stop(); });
    element('retry-transcript').addEventListener('click', transcribeRecording);
    element('replay').addEventListener('click', speakQuestion);
    element('reconnect').addEventListener('click', () => { if (!busy && recorder?.state !== 'recording') connectDevices(); });
    element('camera-toggle').addEventListener('click', () => {
        if (stream?.getVideoTracks().length) {
            stream.getVideoTracks().forEach(track => { stream.removeTrack(track); track.stop(); });
            show('camera-placeholder', true); element('camera').checked = false; element('camera-toggle').textContent = 'Turn camera on';
        } else if (!busy && recorder?.state !== 'recording') { element('camera').checked = true; connectDevices(); }
    });
    element('hide-question').addEventListener('click', () => {
        const concealed = element('question').classList.toggle('spoken-question-concealed');
        element('hide-question').setAttribute('aria-pressed', String(concealed));
        element('hide-question').textContent = concealed ? 'Show question text' : 'Hide question text';
    });
    window.addEventListener('pagehide', () => { cancelWork(); recordingBlob = null; });
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && !element('session').classList.contains('hidden')) {
            cancelWork(); recordingBlob = null; status('Practice paused because the tab was hidden. Devices are off. Reconnect to continue; confirmed answers remain saved.');
        }
    });
});
