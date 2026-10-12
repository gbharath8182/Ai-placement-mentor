import unittest
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
