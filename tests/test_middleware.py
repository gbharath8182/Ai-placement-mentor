import unittest
import logging
from types import SimpleNamespace
from unittest.mock import patch, Mock

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from backend.config import settings
from backend.middleware import SafetyMiddleware


class MiddlewareTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.add_middleware(SafetyMiddleware)

        @self.app.post("/ai/chat")
        async def chat():
            return StreamingResponse(iter([b"data: hello\n\n"]), media_type="text/event-stream")

        @self.app.post("/auth/refresh")
        async def refresh():
            return {"ok": True}

        @self.app.get("/health/live")
        async def health():
            return {"ok": True}

    def test_cookie_request_rejects_cross_origin(self):
        with patch.object(settings, "ALLOWED_ORIGINS", ["https://mentor.test"]), TestClient(self.app) as client:
            self.assertEqual(client.post("/auth/refresh", headers={"Origin": "https://attacker.test"}).status_code, 403)
            self.assertEqual(client.post("/auth/refresh", headers={"Origin": "https://mentor.test"}).status_code, 200)

    def test_api_rate_limit_does_not_block_health(self):
        with patch.object(settings, "API_RATE_LIMIT", 1), TestClient(self.app) as client:
            self.assertEqual(client.post("/ai/chat").status_code, 200)
            response = client.post("/ai/chat")
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.headers["Retry-After"], "60")
            self.assertEqual(client.get("/health/live").status_code, 200)

    def test_stream_and_private_cache_headers(self):
        with TestClient(self.app) as client:
            response = client.post("/ai/chat")
            self.assertEqual(response.text, "data: hello\n\n")
            self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertEqual(response.headers["x-content-type-options"], "nosniff")
            self.assertEqual(response.headers["referrer-policy"], "no-referrer")

    def test_rate_window_expires(self):
        clock = SimpleNamespace(monotonic=Mock(side_effect=[0, 61]))
        with patch.object(settings, "API_RATE_LIMIT", 1), patch("backend.middleware.time", clock), TestClient(self.app) as client:
            self.assertEqual(client.post("/ai/chat").status_code, 200)
            self.assertEqual(client.post("/ai/chat").status_code, 200)

    def test_rejections_keep_security_headers_and_unique_server_request_id(self):
        with TestClient(self.app) as client:
            first = client.post("/auth/refresh", headers={"Origin": "https://attacker.test", "X-Request-ID": "attacker-controlled"})
            second = client.get("/health/live")
            self.assertEqual(first.status_code, 403)
            self.assertEqual(first.headers["cache-control"], "no-store")
            self.assertEqual(first.headers["x-frame-options"], "DENY")
            self.assertEqual(len(first.headers["x-request-id"]), 32)
            self.assertNotEqual(first.headers["x-request-id"], second.headers["x-request-id"])
            self.assertEqual(second.headers["cache-control"], "no-cache")

    def test_authorized_requests_are_not_cached_even_on_other_routes(self):
        with TestClient(self.app) as client:
            response = client.get("/health/live", headers={"Authorization": "Bearer fixture"})
            self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertIn("camera=(self)", response.headers["permissions-policy"])

    def test_search_reads_are_rate_limited_without_blocking_health(self):
        with patch.object(settings, "API_RATE_LIMIT", 1), TestClient(self.app) as client:
            self.assertEqual(client.get("/catalog/search?q=python").status_code, 404)
            response = client.get("/catalog/search?q=python")
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.headers["retry-after"], "60")
            self.assertEqual(client.get("/health/live").status_code, 200)

    def test_request_logs_use_route_template_and_omit_query_and_auth(self):
        @self.app.get("/support/{value}")
        async def support(value: str):
            return {"ok": True}

        with self.assertLogs("uvicorn.error", level=logging.INFO) as captured, TestClient(self.app) as client:
            response = client.get("/support/private-name?token=private-query", headers={"Authorization": "Bearer private-token"})
        output = " ".join(captured.output)
        self.assertIn(response.headers["x-request-id"], output)
        self.assertIn("route=/support/{value}", output)
        self.assertNotIn("private-name", output)
        self.assertNotIn("private-query", output)
        self.assertNotIn("private-token", output)
