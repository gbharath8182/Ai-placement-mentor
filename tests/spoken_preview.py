import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.ai_provider import AIProviderError
from backend.routes import spoken_interview as spoken
from tests.test_spoken_interview import Collection, REVIEW, wav_bytes


def create_app():
    app = FastAPI()
    collections = {"domains": Collection([{"_id": "python", "slug": "python", "title": "Python engineering", "description": "Reason about real systems and the decisions behind your work."}]), "spoken_interview_sessions": Collection()}
    spoken.get_collection = collections.__getitem__
    spoken.settings.GROQ_API_KEY = "offline-fixture-not-a-real-key"

    async def structured(messages, schema, **kwargs):
        data = json.loads(messages[1]["content"])
        count = len(data["previous_turns"])
        question = REVIEW["next_question"] if count == 0 else "For Leaf, how would you evaluate the batching trade-off under a heavier workload?"
        return schema.model_validate({**REVIEW, "next_question": question}), "offline-fixture"

    spoken.provider = SimpleNamespace(structured=structured)
    spoken.audio_provider = SimpleNamespace(speak=AsyncMock(return_value=wav_bytes()), transcribe=AsyncMock(return_value="I built Leaf, an inference engine. I implemented its scheduler and batching strategy."))
    app.include_router(spoken.router)
    app.dependency_overrides[spoken.get_current_user] = lambda: {"id": "fixture-user"}
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/mock-interview")
    def page():
        return FileResponse("frontend/mock-interview.html")

    @app.get("/domains/with-details")
    def domains():
        return list(collections["domains"].documents.values())

    @app.exception_handler(AIProviderError)
    async def provider_error(request, error):
        return JSONResponse({"detail": error.message}, status_code=503)

    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="127.0.0.1", port=8882)
