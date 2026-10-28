import asyncio
import copy
import io
import json
import wave
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.ai_provider import AIProviderError
from backend.interview_audio import InterviewAudio, MAX_AUDIO_BYTES
from backend.routes import spoken_interview as spoken
from tests.test_interview import FakeCollection, FakeCursor


USER = {"id": "candidate-one"}
REVIEW = {"next_question": "You mentioned Leaf. How did you manage inference latency?", "context_quote": "Leaf",
          "clarity": 7, "relevance": 8, "specificity": 6, "technical_reasoning": 7,
          "strengths": ["Explained personal ownership of the scheduler."], "improvements": ["Give a concrete latency measurement."],
          "practice": "Explain the trade-off in ninety seconds, then name one measurement you would collect."}


def wav_bytes():
    output = io.BytesIO()
    with wave.open(output, "wb") as recording:
        recording.setnchannels(1)
        recording.setsampwidth(2)
        recording.setframerate(16000)
        recording.writeframes(b"\x00\x00" * 100)
    return output.getvalue()


class SpokenCursor(FakeCursor):
    def sort(self, *args):
        return self


class Collection(FakeCollection):
    def find(self, query=None, projection=None):
        return SpokenCursor([doc for doc in self.documents.values() if all(doc.get(key) == value for key, value in (query or {}).items())])

    async def delete_one(self, query):
        found = await self.find_one(query)
        if found:
            del self.documents[found["_id"]]
        return SimpleNamespace(deleted_count=int(found is not None))


@pytest.fixture
def context(monkeypatch):
    collections = {"spoken_interview_sessions": Collection(), "domains": Collection([{"_id": "python", "slug": "python", "title": "Python"}])}
    monkeypatch.setattr(spoken, "get_collection", collections.__getitem__)
    monkeypatch.setattr(spoken.settings, "GROQ_API_KEY", "offline-key")
    calls = []

    async def structured(messages, schema, **kwargs):
        calls.append(copy.deepcopy(messages))
        previous = len(json.loads(messages[1]["content"])["previous_turns"])
        next_question = REVIEW["next_question"] if not previous else f"In Leaf, what would you change after design iteration {previous}?"
        return schema.model_validate({**REVIEW, "next_question": next_question}), "fixture-model"

    monkeypatch.setattr(spoken, "provider", SimpleNamespace(structured=AsyncMock(side_effect=structured)))
    audio = SimpleNamespace(speak=AsyncMock(return_value=wav_bytes()), transcribe=AsyncMock(return_value="I built Leaf, an inference engine."))
    monkeypatch.setattr(spoken, "audio_provider", audio)
    app = FastAPI()
    app.include_router(spoken.router)
    app.dependency_overrides[spoken.get_current_user] = lambda: USER

    @app.exception_handler(AIProviderError)
    async def provider_error(request, error):
        return JSONResponse({"detail": error.message}, status_code=503)

    with TestClient(app) as client:
        yield SimpleNamespace(client=client, app=app, sessions=collections["spoken_interview_sessions"], calls=calls, audio=audio)


def start(context, **values):
    result = context.client.post("/mock-interview/spoken/start", json={"domain_slug": "python", "num_questions": 2, "consent": True, **values})
    assert result.status_code == 200, result.text
    return result.json()["session_id"]


def submit(context, identifier, number=1, text="I built Leaf, an inference engine, and implemented its scheduler."):
    return context.client.post("/mock-interview/spoken/answer", json={"session_id": identifier, "question_number": number, "answer": text, "duration_seconds": 35.0, "delivery": "spoken"})


def test_start_requires_explicit_consent_and_authentication(context):
    for value in [False, "true", 1, None]:
        result = context.client.post("/mock-interview/spoken/start", json={"domain_slug": "python", "consent": value})
        assert result.status_code == 422
    context.app.dependency_overrides.clear()
    assert context.client.get("/mock-interview/spoken/capabilities").status_code in {401, 403}
    assert not context.sessions.documents


def test_session_is_separate_scoped_and_does_not_record_camera_or_audio(context):
    identifier = start(context)
    session = context.sessions.documents[identifier]
    assert session["user_id"] == USER["id"] and session["turns"] == []
    assert session["consent_version"] == spoken.NOTICE_VERSION
    assert (session["expires_at"] - session["created_at"]).total_seconds() == 86400
    assert "audio" not in session and "video" not in session


def test_follow_up_contains_current_and_previous_leaf_context(context):
    identifier = start(context, num_questions=3)
    first = submit(context, identifier)
    assert first.status_code == 200
    assert first.json()["question"].startswith("You mentioned Leaf")
    assert "review" not in first.json() and first.json()["summary"] is None
    second = submit(context, identifier, 2, "Leaf uses continuous batching; I measured p95 latency under load.")
    assert second.status_code == 200
    data = json.loads(context.calls[-1][1]["content"])
    assert "inference engine" in data["previous_turns"][0]["answer"]
    assert "continuous batching" in data["candidate_answer"]
    assert "untrusted data" in context.calls[-1][0]["content"]


def test_report_uses_confirmed_answers_with_actionable_feedback_not_gaze_scores(context):
    identifier = start(context)
    assert submit(context, identifier).status_code == 200
    result = submit(context, identifier, 2, "Leaf batches requests and measures latency.")
    assert result.status_code == 200
    report = result.json()["summary"]
    assert result.json()["done"] and report["answered"] == 2
    assert report["scores"]["clarity"] == 7
    assert "latency" in report["turns"][0]["review"]["practice"] or report["turns"][0]["review"]["practice"]
    assert "eye contact" in report["limitations"]
    assert "eye_contact_score" not in json.dumps(report)
    assert submit(context, identifier, 2).status_code == 409


def test_stale_question_and_cross_user_requests_do_not_call_ai_or_audio(context):
    identifier = start(context)
    assert submit(context, identifier, 2).status_code == 409
    context.app.dependency_overrides[spoken.get_current_user] = lambda: {"id": "other-user"}
    for route, body in [("answer", {"session_id": identifier, "question_number": 1, "answer": "Leaf"}), ("speech", {"session_id": identifier, "question_number": 1}), ("end", {"session_id": identifier})]:
        assert context.client.post("/mock-interview/spoken/" + route, json=body).status_code == 404
    assert context.client.get("/mock-interview/spoken/session/" + identifier).status_code == 404
    assert context.client.delete("/mock-interview/spoken/session/" + identifier).status_code == 404
    assert context.client.get("/mock-interview/spoken/sessions").json() == []
    assert context.calls == []
    context.audio.speak.assert_not_awaited()


def test_expired_session_rejects_answers_and_audio(context):
    identifier = start(context)
    context.sessions.documents[identifier]["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert submit(context, identifier).status_code == 409
    assert context.client.post("/mock-interview/spoken/speech", json={"session_id": identifier, "question_number": 1}).status_code == 409
    recovered = context.client.get("/mock-interview/spoken/session/" + identifier).json()
    assert recovered["status"] == "expired" and recovered["summary"]["answered"] == 0


def test_empty_session_has_no_fabricated_scores_and_can_be_deleted(context):
    identifier = start(context)
    result = context.client.post("/mock-interview/spoken/end", json={"session_id": identifier}).json()
    assert all(value is None for value in result["summary"]["scores"].values())
    assert context.client.get("/mock-interview/spoken/session/" + identifier).json()["status"] == "ended"
    assert context.client.delete("/mock-interview/spoken/session/" + identifier).status_code == 200
    assert context.sessions.documents == {}


def test_audio_upload_is_validated_bounded_and_not_submitted(context):
    identifier = start(context)
    base = f"/mock-interview/spoken/transcribe/{identifier}/1"
    assert context.client.post(base, content=b"not audio" * 10, headers={"Content-Type": "audio/webm"}).status_code == 422
    assert context.client.post(base, content=b"video", headers={"Content-Type": "video/webm"}).status_code == 415
    assert context.client.post(base, content=b"x" * (MAX_AUDIO_BYTES + 1), headers={"Content-Type": "audio/wav"}).status_code == 413
    result = context.client.post(base, content=wav_bytes(), headers={"Content-Type": "audio/wav"})
    assert result.status_code == 200
    assert result.json()["submitted"] is False and "Leaf" in result.json()["transcript"]
    assert context.sessions.documents[identifier]["turns"] == []
    context.audio.transcribe.assert_awaited_once()


def test_speech_reads_only_server_question_and_supported_voice(context):
    identifier = start(context, voice="diana")
    result = context.client.post("/mock-interview/spoken/speech", json={"session_id": identifier, "question_number": 1})
    assert result.headers["content-type"] == "audio/wav"
    assert result.headers["cache-control"] == "no-store"
    context.audio.speak.assert_awaited_once_with(spoken.FIRST_QUESTION, "diana")
    assert context.client.post("/mock-interview/spoken/preview-voice", json={"voice": "unknown"}).status_code == 422


def test_context_grounding_rejects_invented_quotes_and_repeated_questions(context, monkeypatch):
    identifier = start(context)
    async def invalid(messages, schema):
        return schema.model_validate({**REVIEW, "context_quote": "I worked at NASA"}), "fixture"
    monkeypatch.setattr(spoken.provider, "structured", invalid)
    with pytest.raises(ValidationError):
        submit(context, identifier)
    assert context.sessions.documents[identifier]["turns"] == []


def test_ai_failure_does_not_advance_or_lose_answer(context, monkeypatch):
    identifier = start(context)
    monkeypatch.setattr(spoken.provider, "structured", AsyncMock(side_effect=AIProviderError("timeout", "Please retry", True)))
    assert submit(context, identifier).status_code == 503
    assert context.sessions.documents[identifier]["version"] == 0


def test_final_answer_does_not_require_an_unused_follow_up(context, monkeypatch):
    identifier = start(context)
    assert submit(context, identifier).status_code == 200
    async def final_review(messages, schema):
        return schema.model_validate({**REVIEW, "next_question": ""}), "fixture"
    monkeypatch.setattr(spoken.provider, "structured", final_review)
    result = submit(context, identifier, 2, "Leaf uses continuous batching.")
    assert result.status_code == 200 and result.json()["done"]


def test_repeated_follow_up_is_rejected_before_committing(context, monkeypatch):
    identifier = start(context)
    async def repeated(messages, schema):
        return schema.model_validate({**REVIEW, "next_question": spoken.FIRST_QUESTION}), "fixture"
    monkeypatch.setattr(spoken.provider, "structured", repeated)
    with pytest.raises(ValidationError):
        submit(context, identifier)
    assert context.sessions.documents[identifier]["turns"] == []


def test_session_path_rejects_invalid_identifiers_before_database_lookup(context):
    assert context.client.get("/mock-interview/spoken/session/invalid$id").status_code == 422
    assert context.client.delete("/mock-interview/spoken/session/invalid$id").status_code == 422


def test_saved_session_list_excludes_answers_and_other_user_data(context):
    identifier = start(context)
    assert submit(context, identifier).status_code == 200
    result = context.client.get("/mock-interview/spoken/sessions").json()
    assert len(result) == 1
    assert "turns" not in result[0] and "answer" not in result[0]
    assert result[0]["session_id"] == identifier


def test_version_conflict_cannot_double_commit(context, monkeypatch):
    identifier = start(context)
    monkeypatch.setattr(context.sessions, "update_one", AsyncMock(return_value=SimpleNamespace(modified_count=0)))
    assert submit(context, identifier).status_code == 409
    assert context.sessions.documents[identifier]["turns"] == []


def test_metrics_are_transcript_estimates_and_typed_answers_have_no_speaking_rate():
    metrics = spoken.answer_metrics("Um I built Leaf. You know, it batches requests.", 30.0, "spoken")
    assert metrics["filler_phrases"] == 2
    assert metrics["estimated_words_per_minute"] > 0
    assert spoken.answer_metrics("Typed answer", 30.0, "typed")["estimated_words_per_minute"] is None
    assert spoken.answer_metrics("Short answer", 1.0, "spoken")["estimated_words_per_minute"] is None


@pytest.mark.parametrize("field,value", [("answer", " "), ("answer", "x" * 6001), ("duration_seconds", float("nan")), ("duration_seconds", 181), ("question_number", 0)])
def test_answer_limits(field, value):
    with pytest.raises(ValidationError):
        spoken.AnswerRequest(**{"session_id": "fixture", "question_number": 1, "answer": "Leaf", field: value})


def test_audio_provider_uses_actual_endpoints_and_does_not_log_input(monkeypatch):
    monkeypatch.setattr(spoken.settings, "GROQ_API_KEY", "offline-key")
    requests = []
    def handle(request):
        requests.append(request)
        return httpx.Response(200, content=wav_bytes()) if request.url.path.endswith("speech") else httpx.Response(200, json={"text": "Leaf inference engine"})
    service = InterviewAudio(httpx.MockTransport(handle))
    assert asyncio.run(service.speak("Tell me about Leaf.", "hannah")) == wav_bytes()
    assert asyncio.run(service.transcribe(wav_bytes(), "audio/wav")) == "Leaf inference engine"
    assert json.loads(requests[0].content)["voice"] == "hannah"
    assert b"whisper-large-v3-turbo" in requests[1].content
    assert all(request.url.host == "api.groq.com" for request in requests)


@pytest.mark.parametrize("status,kind", [(401, "authentication"), (429, "rate_limit"), (500, "service")])
def test_audio_provider_classifies_errors_without_exposing_provider_body(monkeypatch, status, kind):
    monkeypatch.setattr(spoken.settings, "GROQ_API_KEY", "offline-key")
    service = InterviewAudio(httpx.MockTransport(lambda request: httpx.Response(status, text="secret provider diagnostics")))
    with pytest.raises(AIProviderError) as caught:
        asyncio.run(service.speak("Question?", "hannah"))
    assert caught.value.kind == kind and "secret" not in caught.value.message


def test_audio_provider_rejects_invalid_audio_and_transcription(monkeypatch):
    monkeypatch.setattr(spoken.settings, "GROQ_API_KEY", "offline-key")
    service = InterviewAudio(httpx.MockTransport(lambda request: httpx.Response(200, content=b"<html>bad</html>")))
    with pytest.raises(AIProviderError):
        asyncio.run(service.speak("Question?", "hannah"))
    with pytest.raises(AIProviderError):
        asyncio.run(service.transcribe(wav_bytes(), "audio/wav"))


def test_voice_model_terms_have_an_actionable_error(monkeypatch):
    monkeypatch.setattr(spoken.settings, "GROQ_API_KEY", "offline-key")
    service = InterviewAudio(httpx.MockTransport(lambda request: httpx.Response(400, json={"error": {"code": "model_terms_required", "message": "private diagnostics"}})))
    with pytest.raises(AIProviderError) as caught:
        asyncio.run(service.speak("Question?", "hannah"))
    assert caught.value.kind == "model_terms_required"
    assert "accept" in caught.value.message and "private" not in caught.value.message
