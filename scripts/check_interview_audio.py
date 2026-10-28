import argparse
import asyncio

from backend.ai_provider import AIProviderError
from backend.interview_audio import audio_provider


async def check():
    try:
        content = await audio_provider.speak("Hello. Tell me about a project you are proud of, and the decisions you made while building it.", "hannah")
        transcript = await audio_provider.transcribe(content, "audio/wav")
        print({"speech": "passed", "voice": "hannah", "transcription": "passed", "transcript_characters": len(transcript)})
        return 0
    except AIProviderError as error:
        print({"audio_check": "failed", "code": error.kind, "message": error.message})
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="One synthetic TTS and STT round-trip. Uses configured Groq credentials, incurs provider usage, sends no candidate data, saves no audio.")
    parser.add_argument("--confirm-provider-call", action="store_true")
    arguments = parser.parse_args()
    if not arguments.confirm_provider_call:
        parser.error("Pass --confirm-provider-call to authorize the synthetic provider round-trip")
    raise SystemExit(asyncio.run(check()))
