# Spoken interview practice

## Candidate workflow

Open **Mock interviews**, choose a domain and select **Camera & voice**. Choose 3, 5 or 8 questions, optionally enter a target role, and audition Hannah, Diana or Autumn. The voices use Groq-hosted Orpheus English, not browser speech synthesis or an imitation of a real person. Voice preference is subjective; audition before starting.

Read and accept the audio/transcript notice before enabling devices. Camera is optional; the microphone and local camera mirror require HTTPS or localhost and browser permission. Wear headphones. Press **Record answer**, explain your answer, then **Stop & transcribe**. Correct names and technical terms in the transcript before sending. The AI asks a contextual follow-up using the confirmed conversation rather than selecting unrelated canned questions. For example, discussing Leaf as an inference engine can lead to questions about its scheduler, latency, batching and evaluation.

This is a turn-based spoken practice session, not a live video call, human interviewer, continuous-listening agent or WebRTC conferencing service. There is no automatic answer submission. Typed answers remain available when recording or voice playback fails. Replay reuses the current question's audio in the browser. Failed transcription can be retried without re-recording. Back/Resume recovers committed progress after a lost response; unsent text and raw recordings are not durably saved.

End the session to receive per-answer strengths, improvements and practice exercises, plus clarity, relevance, specificity and reasoning guidance. Estimated word rate uses recording duration, including pauses; filler counts use the edited transcript. These are not acoustic measurements or calibrated hiring scores. No gaze, accent, emotion, confidence, personality or appearance assessment is performed.

## Privacy and lifecycle

- Camera video remains local. Only microphone audio is recorded; there is no video upload or recording endpoint.
- Each recording is limited to three minutes/8 MB. Audio is sent through the authenticated application server to Groq for transcription, kept transiently and not persisted by the app. Groq's own [data policy](https://console.groq.com/docs/your-data) applies.
- Confirmed answers, contextual references, feedback and transcript-based metrics are stored in a new user-scoped `spoken_interview_sessions` collection in the existing configured database. No content migration or changes to existing interview records are required.
- Active sessions accept answers for 24 hours. Expiry prevents further answers; it does not erase a transcript. Recent sessions (up to 50) can be resumed/reviewed or deleted. Application deletion does not retroactively remove operator backups or provider-retained data.
- Devices and playback stop when leaving the studio, ending the session, navigating away or hiding the tab. Hidden-tab pauses discard an unfinished recording; reconnect to continue. Permission denial and device disconnection are explicit states, not evidence of user performance.
- Browser session storage holds a user-keyed session identifier, not a durable transcript. Authentication and ownership are checked server-side on every session/audio route. Concurrent/stale answers cannot overwrite committed turns.

## Deployment

The existing `GROQ_API_KEY` can serve chat, transcription and speech if that key's organization has access to all selected models. A new key is not needed merely because voice mode was added. Keep keys server-side.

Optional settings (defaults shown):

```dotenv
GROQ_STT_MODEL=whisper-large-v3-turbo
GROQ_TTS_MODEL=canopylabs/orpheus-v1-english
INTERVIEW_AUDIO_TIMEOUT_SECONDS=45
```

An organization administrator must review and accept Orpheus English model terms in the [Groq Playground](https://console.groq.com/playground?model=canopylabs%2Forpheus-v1-english). The documentation page does not itself accept them. The app reports `model_terms_required` explicitly. Access, quotas and provider billing still apply. The supported voice choices and question limit target this English Orpheus model; changing models requires corresponding compatibility testing, not just swapping an arbitrary model identifier.

All provider calls use HTTPS and work without Render SMTP/WebSocket services. The implementation uses existing HTTP requests and no new paid hosting service. Render Free cold starts and provider processing can introduce pauses; this is not a low-latency streaming-voice guarantee. Do not add a collection seed to the build command. MongoDB creates new session records lazily on actual use.

## Verification

`python -m pytest tests/test_spoken_interview.py` covers ownership, strict consent, context grounding, expiry, stale/version conflicts, bounds, deletion, audio errors and transcript-only metrics. The full existing text interview suite remains separate and unchanged.

For isolated browser QA, run `python -m tests.spoken_preview`, then `node scripts/spoken_smoke.cjs PATH_TO_PLAYWRIGHT http://127.0.0.1:8882`. The server binds to loopback, replaces authentication/AI/database with fixtures and must never be deployed. Edge uses synthetic media devices, not the owner's camera/microphone. Screenshots remain under ignored `artifacts/spoken/`. Stop the fixture server afterward.

`python -m scripts.check_interview_audio --confirm-provider-call` makes one synthetic voice/transcription round-trip with the configured Groq key, consumes provider usage, saves no audio and sends no candidate data. It is a separate live test, not part of offline CI.

References: [Groq transcription](https://console.groq.com/docs/speech-to-text), [Orpheus speech and voices](https://console.groq.com/docs/text-to-speech/orpheus).
