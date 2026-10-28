import io
import json
import wave

import httpx

from backend.ai_provider import AIProviderError, API_URL, classify_error
from backend.config import settings


VOICES = {"autumn": "Autumn", "diana": "Diana", "hannah": "Hannah"}
MAX_AUDIO_BYTES = 8 * 1024 * 1024
AUDIO_TYPES = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "mp4", "audio/wav": "wav", "audio/mpeg": "mp3"}


class InterviewAudio:
    def __init__(self, transport=None):
        self.transport = transport

    async def request(self, endpoint, **arguments):
        if not settings.GROQ_API_KEY:
            raise AIProviderError("not_configured", "Spoken interviews need administrator-configured Groq audio access.")
        try:
            async with httpx.AsyncClient(transport=self.transport, timeout=httpx.Timeout(settings.INTERVIEW_AUDIO_TIMEOUT_SECONDS, connect=8), follow_redirects=False) as client:
                async with client.stream("POST", API_URL + endpoint, headers={"Authorization": "Bearer " + settings.GROQ_API_KEY}, **arguments) as response:
                    if response.status_code != 200:
                        details = bytearray()
                        async for chunk in response.aiter_bytes():
                            details.extend(chunk[:max(0, 8192 - len(details))])
                            if len(details) >= 8192:
                                break
                        try:
                            code = json.loads(details).get("error", {}).get("code")
                        except (ValueError, AttributeError):
                            code = None
                        if code == "model_terms_required":
                            raise AIProviderError("model_terms_required", "The administrator must accept the Orpheus English model terms in the Groq console before interviewer voice playback is enabled.")
                        raise classify_error(response.status_code)
                    chunks = []
                    size = 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > MAX_AUDIO_BYTES:
                            raise AIProviderError("invalid_response", "The audio service returned too much data. Please retry.", True)
                        chunks.append(chunk)
                    return b"".join(chunks)
        except httpx.TimeoutException:
            raise AIProviderError("timeout", "Audio processing took too long. Your answer has not been submitted; please retry.", True) from None
        except httpx.RequestError:
            raise AIProviderError("network", "The audio connection was interrupted. Please retry.", True) from None

    async def transcribe(self, content, content_type):
        data = await self.request("/audio/transcriptions", files={"file": ("answer." + AUDIO_TYPES[content_type], content, content_type)},
                                  data={"model": settings.GROQ_STT_MODEL, "response_format": "json", "language": "en", "temperature": "0"})
        try:
            text = json.loads(data)["text"]
            if not isinstance(text, str) or not text.strip() or len(text) > 6000:
                raise ValueError
            return text.strip()
        except (ValueError, KeyError, TypeError):
            raise AIProviderError("invalid_response", "No usable transcript was returned. Retry recording or type your answer.", True) from None

    async def speak(self, text, voice):
        if voice not in VOICES or not 1 <= len(text) <= 200:
            raise ValueError("Unsupported voice or question length")
        data = await self.request("/audio/speech", json={"model": settings.GROQ_TTS_MODEL, "input": text, "voice": voice, "response_format": "wav"})
        try:
            with wave.open(io.BytesIO(data), "rb") as recording:
                if recording.getnframes() == 0 or recording.getnchannels() > 2:
                    raise ValueError
        except (wave.Error, EOFError, ValueError):
            raise AIProviderError("invalid_response", "The interviewer audio was incomplete. Replay the question or continue with its text.", True) from None
        return data


audio_provider = InterviewAudio()
