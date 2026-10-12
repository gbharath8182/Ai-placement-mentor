import asyncio
import copy
import json
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo.errors import OperationFailure

from backend import auth, database, main
from backend.ai_provider import AIProviderError, Completion, GroqProvider
from backend.config import settings
from backend.routes import ai


USER = {"id": "000000000000000000000001", "profile": {"experience_level": "fresher"}}
OTHER_USER = {"id": "000000000000000000000002", "profile": {"experience_level": "experienced"}}
TOPIC = {
    "_id": ObjectId("000000000000000000000010"), "slug": "integration-python-topic",
    "domain_slug": "integration-domain", "title": "Integration lesson", "difficulty": "beginner",
    "content_blocks": [], "subtopics": [
        {"title": "Selected section", "content_blocks": [
            {"type": "text", "value": "SELECTED_REFERENCE: names refer to objects."},
            {"type": "code", "language": "python", "value": "selected_example = 42"},
        ]},
        {"title": "Other section", "content_blocks": [
            {"type": "text", "value": "UNSELECTED_REFERENCE: unrelated loop material."},
        ]},
    ],
}
RAW_FAILURE = "upstream-private-secret database credentials private-user private-password private-host private-db"
REAL_ASYNC_CLIENT = httpx.AsyncClient


class Cursor:
    def __init__(self, documents):
        self.documents = copy.deepcopy(documents)
        self.maximum = len(self.documents)

    def limit(self, maximum):
        self.maximum = maximum
        return self

    def max_time_ms(self, timeout):
        return self

    def __aiter__(self):
        async def iterate():
            for document in self.documents[:self.maximum]:
                yield copy.deepcopy(document)
        return iterate()


class Collection:
    def __init__(self, documents=()):
        self.documents = copy.deepcopy(list(documents))
        self.find_one = AsyncMock(side_effect=self._find_one)
        self.find = Mock(side_effect=self._find)
        self.update_one = AsyncMock(side_effect=self._update_one)

    def _matches(self, document, query):
        if any(isinstance(value, dict) for value in query.values()):
            raise AssertionError("Unexpected MongoDB query operator")
        return all(document.get(key) == value for key, value in query.items())

    async def _find_one(self, query):
        return next((copy.deepcopy(document) for document in self.documents if self._matches(document, query)), None)

    def _find(self, query=None, projection=None):
        return Cursor([document for document in self.documents if self._matches(document, query or {})])

    async def _update_one(self, query, update, upsert=False):
        document = next((document for document in self.documents if self._matches(document, query)), None)
        if document is None:
            if not upsert:
                return SimpleNamespace(modified_count=0)
            document = {"_id": ObjectId(), **copy.deepcopy(query)}
            self.documents.append(document)
        for operation, changes in update.items():
            if operation == "$push":
                for field, specification in changes.items():
                    document[field] = document.get(field, []) + copy.deepcopy(specification["$each"])
                    if "$slice" in specification:
                        document[field] = document[field][specification["$slice"]:]
            elif operation == "$set":
                document.update(copy.deepcopy(changes))
            else:
                raise AssertionError("Unexpected test database update: " + operation)
        return SimpleNamespace(modified_count=1)


def sse_events(text):
    events = []
    for frame in text.split("\n\n"):
        if not frame.strip():
            continue
        if not frame.startswith("data: "):
            raise AssertionError("Invalid SSE frame: " + frame)
        payload = frame[6:].strip()
        events.append("[DONE]" if payload == "[DONE]" else json.loads(payload))
    return events


class APIFixture:
    def setUp(self):
        super().setUp()
        self.current_user = copy.deepcopy(USER)
        self.collections = {
            "topics": Collection([TOPIC]), "chat_sessions": Collection(),
            "user_progress": Collection(), "users": Collection(),
        }
        self.sessions = self.collections["chat_sessions"]
        self.connect = Mock()
        self.ping = AsyncMock(return_value=True)
        self.disconnect = Mock()
        self.replace(main.db_client, "connect", self.connect)
        self.replace(main.db_client, "ping", self.ping)
        self.replace(main.db_client, "disconnect", self.disconnect)
        self.replace(main.db_client, "db", self.collections)
        self.replace(main.db_client, "client", None)
        self.replace(database, "AsyncIOMotorClient", Mock(side_effect=AssertionError("External MongoDB access is forbidden")))
        self.replace(settings, "JWT_SECRET", "offline-api-tests-only-signing-key-at-least-32-characters")
        self.replace(settings, "APP_ENV", "test")
        self.replace(settings, "GROQ_API_KEY", "offline-api-test-key")
        self.replace(settings, "GROQ_MAX_RETRIES", 0)
        self.replace(settings, "API_RATE_LIMIT", 100000)
        self.replace(settings, "AUTH_RATE_LIMIT", 100000)
        self.replace(settings, "ALLOWED_ORIGINS", ["http://testserver"])
        self.replace(main.app, "middleware_stack", None)
        self.replace(main.app, "dependency_overrides", {auth.get_current_user: self.authenticated_user})
        self.provider = SimpleNamespace(
            complete=AsyncMock(return_value=Completion("An evidence-grounded explanation.", "offline-selected-model")),
            stream=Mock(side_effect=self.successful_stream),
        )
        self.replace(ai, "provider", self.provider)
        self.replace(httpx, "AsyncClient", self.offline_async_client)

    def replace(self, target, attribute, value):
        replacement = patch.object(target, attribute, value)
        replacement.start()
        self.addCleanup(replacement.stop)

    async def authenticated_user(self):
        return copy.deepcopy(self.current_user)

    def offline_async_client(self, *args, **kwargs):
        if not isinstance(kwargs.get("transport"), (httpx.MockTransport, httpx.ASGITransport)):
            raise AssertionError("External HTTP access is forbidden")
        return REAL_ASYNC_CLIENT(*args, **kwargs)

    async def successful_stream(self, messages):
        yield "Grounded "
        yield "reply."

    def client(self, **kwargs):
        return TestClient(main.app, headers={"Origin": "http://testserver"}, **kwargs)

    def chat_request(self, **overrides):
        return {"topic_slug": TOPIC["slug"], "message": "Explain the example", **overrides}

    def seed_history(self, user=USER, topic_slug=None, messages=None):
        document = {
            "_id": ObjectId(), "user_id": ObjectId(user["id"]), "topic_slug": topic_slug or TOPIC["slug"],
            "messages": copy.deepcopy(messages if messages is not None else [
                {"role": "user", "content": "Earlier question"}, {"role": "assistant", "content": "Earlier reply"},
            ]),
        }
        self.sessions.documents.append(document)
        return copy.deepcopy(document)


class APIIntegrationTests(APIFixture, unittest.TestCase):
    def test_public_landing_and_learn_do_not_require_authentication_or_database(self):
        main.app.dependency_overrides.clear()
        with self.client(follow_redirects=False) as client:
            for path in ["/", "/learn"]:
                with self.subTest(path=path):
                    response = client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn("text/html", response.headers["content-type"])
                    self.assertIn("<h1", response.text)
                    self.assertIn("AI Placement Mentor", response.text)
                    self.assertNotIn("location", response.headers)
                    self.assertEqual(response.headers["x-content-type-options"], "nosniff")
            self.assertIn('href="/learn"', client.get("/").text)
        for collection in self.collections.values():
            collection.find_one.assert_not_awaited()
            collection.find.assert_not_called()
            collection.update_one.assert_not_awaited()

    def test_lifespan_uses_only_mocked_database_lifecycle(self):
        self.connect.assert_not_called()
        with self.client() as client:
            self.connect.assert_called_once_with()
            self.ping.assert_awaited_once_with()
            self.disconnect.assert_not_called()
            self.assertEqual(client.get("/health/live").status_code, 200)
        self.disconnect.assert_called_once_with()

    def test_liveness_is_independent_of_readiness(self):
        self.ping.return_value = False
        with self.client() as client:
            response = client.get("/health/live")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "ok")
            self.ping.assert_awaited_once_with()

    def test_readiness_reports_failure_and_recovery_without_reconnecting(self):
        self.ping.side_effect = [False, False, True, False, True]
        with self.client() as client:
            for ready in [False, True, False, True]:
                with self.subTest(ready=ready):
                    response = client.get("/health/ready")
                    self.assertEqual(response.status_code, 200 if ready else 503)
                    self.assertEqual(response.json(), {
                        "status": "ready" if ready else "unavailable",
                        "database": "connected" if ready else "unavailable",
                    })
            self.assertEqual(self.ping.await_count, 5)
            self.connect.assert_called_once_with()

    def test_database_exceptions_are_safe_503_responses(self):
        with self.client() as client:
            self.sessions.find_one.side_effect = OperationFailure(RAW_FAILURE)
            response = client.get("/ai/history/" + TOPIC["slug"])
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()["error"], {"code": "database", "retryable": True})
            self.assertNotIn(RAW_FAILURE, response.text)
            self.assertNotIn("private-password", response.text)
            self.assertIn("temporarily unavailable", response.json()["detail"])
            self.assertIn("no-store", response.headers["cache-control"])
            self.collections["topics"].find_one.side_effect = OperationFailure(RAW_FAILURE)
            response = client.post("/ai/explain", json={"topic_slug": TOPIC["slug"], "level": "fresher"})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("private-host", response.text)
            self.assertEqual(client.get("/health/live").status_code, 200)
        self.provider.complete.assert_not_awaited()

    def test_ai_routes_require_authentication_before_provider_or_database_calls(self):
        main.app.dependency_overrides.clear()
        endpoints = [
            ("/ai/explain", {"topic_slug": TOPIC["slug"], "level": "fresher"}),
            ("/ai/recommend", {"topic_slug": TOPIC["slug"], "answers": {}}),
            ("/ai/chat", self.chat_request()),
        ]
        with self.client() as client:
            for path, payload in endpoints:
                for headers in [{}, {"Authorization": "Bearer not-a-valid-token"}]:
                    with self.subTest(path=path, headers=headers):
                        response = client.post(path, json=payload, headers=headers)
                        self.assertEqual(response.status_code, 401)
                        self.assertNotIn(settings.JWT_SECRET, response.text)
            self.assertEqual(client.get("/ai/history/" + TOPIC["slug"]).status_code, 401)
        self.provider.complete.assert_not_awaited()
        self.provider.stream.assert_not_called()
        for collection in self.collections.values():
            collection.find_one.assert_not_awaited()
            collection.find.assert_not_called()

    def test_explain_and_recommend_upstream_authentication_errors_are_sanitized(self):
        calls = []

        def unauthorized(request):
            calls.append(request)
            return httpx.Response(401, text=RAW_FAILURE)

        self.replace(ai, "provider", GroqProvider(httpx.MockTransport(unauthorized)))
        with self.client() as client:
            for endpoint, payload in [
                ("explain", {"topic_slug": TOPIC["slug"], "level": "fresher"}),
                ("recommend", {"topic_slug": TOPIC["slug"], "answers": {"confidence": "unsure"}}),
            ]:
                with self.subTest(endpoint=endpoint):
                    response = client.post("/ai/" + endpoint, json=payload)
                    self.assertEqual(response.status_code, 503)
                    self.assertEqual(response.json()["error"]["code"], "authentication")
                    self.assertFalse(response.json()["error"]["retryable"])
                    self.assertIn("administrator", response.json()["detail"])
                    self.assertNotIn(RAW_FAILURE, response.text)
                    self.assertNotIn("private-password", response.text)
                    self.assertNotIn("offline-api-test-key", response.text)
                    self.assertNotIn("explanation" if endpoint == "explain" else "recommendation", response.json())
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(request.headers["authorization"] == "Bearer offline-api-test-key" for request in calls))

    def test_provider_rate_limit_uses_global_safe_error_handler(self):
        self.provider.complete.side_effect = AIProviderError("rate_limit", "The assistant is busy. Please retry.", True)
        with self.client() as client:
            response = client.post("/ai/explain", json={"topic_slug": TOPIC["slug"], "level": "fresher"})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"]["code"], "rate_limit")
        self.assertTrue(response.json()["error"]["retryable"])

    def test_explain_and_recommend_success_are_grounded_in_loaded_topic(self):
        with self.client() as client:
            explained = client.post("/ai/explain", json={"topic_slug": TOPIC["slug"], "level": "experienced"})
            recommended = client.post("/ai/recommend", json={"topic_slug": TOPIC["slug"], "answers": {"goal": "Review names"}})
        self.assertEqual(explained.status_code, 200)
        self.assertEqual(recommended.status_code, 200)
        self.assertEqual(explained.json()["explanation"], "An evidence-grounded explanation.")
        self.assertEqual(recommended.json()["recommendation"], "An evidence-grounded explanation.")
        explanation_call, recommendation_call = self.provider.complete.await_args_list
        self.assertEqual(explanation_call.kwargs["model"], settings.GROQ_FALLBACK_MODEL)
        for call in [explanation_call, recommendation_call]:
            self.assertIn("SELECTED_REFERENCE", call.args[0][0]["content"])
        self.assertIn(TOPIC["slug"], recommendation_call.args[0][0]["content"])
        self.assertIn("Review names", recommendation_call.args[0][0]["content"])

    def test_successful_sse_chat_saves_one_complete_user_assistant_pair(self):
        original = self.seed_history()

        async def stream(messages):
            self.sessions.update_one.assert_not_awaited()
            yield "Grounded "
            self.sessions.update_one.assert_not_awaited()
            yield "reply."

        self.provider.stream.side_effect = stream
        with self.client() as client:
            response = client.post("/ai/chat", json=self.chat_request())
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])
        events = sse_events(response.text)
        self.assertEqual(events[-1], "[DONE]")
        chunks = [event["choices"][0]["delta"]["content"] for event in events[:-1]]
        self.assertEqual("".join(chunks), "Grounded reply.")
        self.sessions.update_one.assert_awaited_once()
        saved = self.sessions.documents[0]["messages"]
        self.assertEqual(saved[:-2], original["messages"])
        self.assertEqual([(message["role"], message["content"]) for message in saved[-2:]], [
            ("user", "Explain the example"), ("assistant", "Grounded reply."),
        ])
        self.assertIsInstance(saved[-1]["ts"], datetime)
        self.assertIsNotNone(saved[-1]["ts"].tzinfo)
        update = self.sessions.update_one.await_args
        self.assertEqual(update.args[0], {"user_id": ObjectId(USER["id"]), "topic_slug": TOPIC["slug"]})
        self.assertTrue(update.kwargs["upsert"])
        self.assertEqual(update.args[1]["$push"]["messages"]["$slice"], -40)
        supplied = self.provider.stream.call_args.args[0]
        self.assertEqual(supplied[1:-1], original["messages"])
        self.assertEqual(supplied[-1], {"role": "user", "content": "Explain the example"})

    def test_failed_and_partial_failed_streams_do_not_persist_fabricated_pairs(self):
        original = self.seed_history()
        with self.client() as client:
            for partial in [False, True]:
                with self.subTest(partial=partial):
                    async def failed(messages):
                        if partial:
                            yield "Unfinished draft"
                        raise AIProviderError("network", "The assistant connection was interrupted. Please retry.", True) from RuntimeError(RAW_FAILURE)

                    self.provider.stream.side_effect = failed
                    response = client.post("/ai/chat", json=self.chat_request())
                    events = sse_events(response.text)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(events[-1]["error"]["code"], "network")
                    self.assertTrue(events[-1]["error"]["retryable"])
                    self.assertNotIn("[DONE]", events)
                    self.assertNotIn(RAW_FAILURE, response.text)
                    if partial:
                        self.assertEqual(events[0]["choices"][0]["delta"]["content"], "Unfinished draft")
                    else:
                        self.assertFalse(any("choices" in event for event in events))
                    self.assertEqual(self.sessions.documents, [original])
        self.sessions.update_one.assert_not_awaited()

    def test_database_failure_after_stream_is_safe_and_does_not_save_pair(self):
        original = self.seed_history()
        self.sessions.update_one.side_effect = OperationFailure(RAW_FAILURE)
        with self.client() as client:
            response = client.post("/ai/chat", json=self.chat_request())
        events = sse_events(response.text)
        self.assertEqual(events[-1]["error"]["code"], "database")
        self.assertTrue(events[-1]["error"]["retryable"])
        self.assertNotIn("[DONE]", events)
        self.assertNotIn(RAW_FAILURE, response.text)
        self.assertEqual(self.sessions.documents, [original])

    def test_history_and_chat_are_scoped_to_user_and_topic(self):
        own = self.seed_history(messages=[{"role": "assistant", "content": "OWN_HISTORY"}])
        other = self.seed_history(OTHER_USER, messages=[{"role": "assistant", "content": "OTHER_USER_HISTORY"}])
        self.seed_history(topic_slug="other-topic", messages=[{"role": "assistant", "content": "OTHER_TOPIC_HISTORY"}])
        with self.client() as client:
            response = client.get("/ai/history/" + TOPIC["slug"])
            self.assertEqual(response.json()["messages"], own["messages"])
            client.post("/ai/chat", json=self.chat_request())
            prompt = json.dumps(self.provider.stream.call_args.args[0])
            self.assertIn("OWN_HISTORY", prompt)
            self.assertNotIn("OTHER_USER_HISTORY", prompt)
            self.assertNotIn("OTHER_TOPIC_HISTORY", prompt)
            self.current_user = copy.deepcopy(OTHER_USER)
            response = client.get("/ai/history/" + TOPIC["slug"])
            self.assertEqual(response.json()["messages"], other["messages"])
        self.assertEqual(self.sessions.documents[1], other)
        self.assertEqual(self.sessions.find_one.await_args.args[0]["user_id"], ObjectId(OTHER_USER["id"]))

    def test_history_limits_and_public_message_shape(self):
        messages = [{"role": "user" if index % 2 == 0 else "assistant", "content": "message-" + str(index),
                     "ts": "private-timestamp", "private_metadata": "not-public"} for index in range(30)]
        self.seed_history(messages=messages)
        with self.client() as client:
            response = client.get("/ai/history/" + TOPIC["slug"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["messages"], [{"role": message["role"], "content": message["content"]} for message in messages[-20:]])
        self.sessions.update_one.assert_not_awaited()

    def test_selected_subtopic_grounding_excludes_unselected_material(self):
        with self.client() as client:
            response = client.post("/ai/chat", json=self.chat_request(subtopic_title="Selected section"))
        self.assertEqual(response.status_code, 200)
        prompt = self.provider.stream.call_args.args[0][0]["content"]
        self.assertIn("SELECTED_REFERENCE", prompt)
        self.assertIn("selected_example = 42", prompt)
        self.assertNotIn("UNSELECTED_REFERENCE", prompt)
        self.assertIn("Selected section", prompt)

    def test_unknown_subtopic_is_rejected_without_streaming_or_persistence(self):
        with self.client() as client:
            response = client.post("/ai/chat", json=self.chat_request(subtopic_title="Invented section"))
        self.assertEqual(response.status_code, 422)
        self.provider.stream.assert_not_called()
        self.sessions.find_one.assert_not_awaited()
        self.sessions.update_one.assert_not_awaited()

    def test_malformed_topic_slug_inputs_are_rejected_before_lookup(self):
        malformed = [{"$ne": None}, [TOPIC["slug"]], None, 123, "", "x" * 129]
        requests = [
            ("/ai/chat", self.chat_request()),
            ("/ai/explain", {"topic_slug": TOPIC["slug"], "level": "fresher"}),
            ("/ai/recommend", {"topic_slug": TOPIC["slug"], "answers": {}}),
        ]
        with self.client() as client:
            for path, payload in requests:
                for slug in malformed:
                    with self.subTest(path=path, slug=slug):
                        response = client.post(path, json={**payload, "topic_slug": slug})
                        self.assertEqual(response.status_code, 422)
        self.collections["topics"].find_one.assert_not_awaited()
        self.provider.complete.assert_not_awaited()
        self.provider.stream.assert_not_called()
        self.sessions.update_one.assert_not_awaited()

    def test_reading_preserves_legacy_completed_progress(self):
        legacy = {"_id": ObjectId(), "user_id": ObjectId(USER["id"]), "topic_slug": TOPIC["slug"],
                  "status": "completed", "ai_notes": "Legacy completion before assessment evidence"}
        progress = self.collections["user_progress"]
        progress.documents.append(copy.deepcopy(legacy))
        with self.client() as client:
            lesson = client.get("/topics/" + TOPIC["slug"])
            self.assertEqual(lesson.status_code, 200)
            response = client.post("/progress/update", json={"topic_slug": TOPIC["slug"], "status": "in_progress"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "completed")
            listed = client.get("/progress/" + USER["id"])
            self.assertEqual(listed.status_code, 200)
            self.assertTrue(any(document["topic_slug"] == TOPIC["slug"] and document["status"] == "completed" for document in listed.json()))
        self.assertEqual(progress.documents, [legacy])
        progress.update_one.assert_not_awaited()
        self.assertEqual(progress.find_one.await_args.args[0], {"user_id": ObjectId(USER["id"]), "topic_slug": TOPIC["slug"]})

    def test_whitespace_topic_slugs_are_validation_errors_not_server_errors(self):
        requests = [
            ("/ai/chat", self.chat_request()),
            ("/ai/explain", {"topic_slug": TOPIC["slug"], "level": "fresher"}),
            ("/ai/recommend", {"topic_slug": TOPIC["slug"], "answers": {}}),
        ]
        with self.client(raise_server_exceptions=False) as client:
            for path, payload in requests:
                with self.subTest(path=path):
                    response = client.post(path, json={**payload, "topic_slug": " \t\n "})
                    self.assertEqual(response.status_code, 422)
        self.collections["topics"].find_one.assert_not_awaited()
        self.provider.complete.assert_not_awaited()
        self.provider.stream.assert_not_called()

    def test_origin_guard_remains_enabled(self):
        with self.client() as client:
            response = client.post("/ai/chat", json=self.chat_request(), headers={"Origin": "https://untrusted.example"})
        self.assertEqual(response.status_code, 403)
        self.provider.stream.assert_not_called()
        self.sessions.update_one.assert_not_awaited()

    def test_rate_limit_guard_remains_enabled(self):
        self.replace(settings, "API_RATE_LIMIT", 1)
        with self.client() as client:
            first = client.post("/ai/explain", json={"topic_slug": TOPIC["slug"], "level": "fresher"})
            second = client.post("/ai/explain", json={"topic_slug": TOPIC["slug"], "level": "fresher"})
            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 429)
            self.assertEqual(second.headers["retry-after"], "60")
            self.assertEqual(client.get("/health/live").status_code, 200)
        self.provider.complete.assert_awaited_once()

    def test_public_curriculum_catalog_is_available_without_auth_or_exact_counts(self):
        main.app.dependency_overrides.clear()
        with self.client() as client:
            response = client.get("/curriculum")
            self.assertEqual(response.status_code, 200)
            catalog = response.json()
            self.assertTrue(catalog["domains"])
            self.assertTrue(catalog["topics"])
            domain_slugs = {domain["slug"] for domain in catalog["domains"]}
            for topic in catalog["topics"]:
                self.assertIn(topic["domain_slug"], domain_slugs)
                self.assertTrue(topic["objectives"])
            published = client.get("/topics/" + catalog["topics"][0]["slug"])
            self.assertEqual(published.status_code, 200)
            lesson = published.json()
            sections = [lesson] + (lesson.get("subtopics") or [])
            for section in sections:
                for block in section.get("content_blocks") or []:
                    if block.get("type") == "knowledge_check":
                        self.assertNotIn("correct_index", block)
                        self.assertNotIn("explanation", block)
        self.collections["users"].find_one.assert_not_awaited()


class APIStreamCancellationTests(APIFixture, unittest.IsolatedAsyncioTestCase):
    async def test_cancelling_partial_asgi_stream_persists_neither_message(self):
        original = self.seed_history()
        first_token, stream_closed = asyncio.Event(), asyncio.Event()
        wait_forever = asyncio.Event()
        sent = []

        async def partial_stream(messages):
            try:
                yield "Unfinished partial response"
                await wait_forever.wait()
            finally:
                stream_closed.set()

        self.provider.stream.side_effect = partial_stream
        body = json.dumps(self.chat_request()).encode()
        scope = {
            "type": "http", "asgi": {"version": "3.0", "spec_version": "2.0"},
            "http_version": "1.1", "method": "POST", "scheme": "http", "path": "/ai/chat",
            "raw_path": b"/ai/chat", "query_string": b"", "root_path": "",
            "headers": [(b"host", b"testserver"), (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode()), (b"origin", b"http://testserver")],
            "client": ("cancelled-test-client", 1234), "server": ("testserver", 80),
        }
        received_request = False

        async def receive():
            nonlocal received_request
            if not received_request:
                received_request = True
                return {"type": "http.request", "body": body, "more_body": False}
            await wait_forever.wait()
            return {"type": "http.disconnect"}

        async def send(message):
            sent.append(copy.deepcopy(message))
            if message["type"] == "http.response.body" and b"Unfinished partial response" in message.get("body", b""):
                first_token.set()

        async with main.lifespan(main.app):
            task = asyncio.create_task(main.app(scope, receive, send))
            try:
                await asyncio.wait_for(first_token.wait(), timeout=3)
            finally:
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
            await asyncio.wait_for(stream_closed.wait(), timeout=3)
        self.assertEqual(self.sessions.documents, [original])
        self.sessions.update_one.assert_not_awaited()
        started = next(message for message in sent if message["type"] == "http.response.start")
        self.assertEqual(started["status"], 200)
        response_body = b"".join(message.get("body", b"") for message in sent).decode()
        self.assertIn("Unfinished partial response", response_body)
        self.assertNotIn("[DONE]", response_body)
        self.connect.assert_called_once_with()
        self.disconnect.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
