import asyncio
import json
import unittest
from unittest.mock import patch

import httpx
from pydantic import BaseModel, Field

from backend.ai_provider import GroqProvider, AIProviderError
from backend.config import settings


class Grade(BaseModel):
    score: int = Field(ge=0, le=10, strict=True)


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.patches = [patch.object(settings, "GROQ_API_KEY", "test-key"), patch.object(settings, "GROQ_MAX_RETRIES", 1)]
        for replacement in self.patches:
            replacement.start()
            self.addCleanup(replacement.stop)
        self.calls = []

    def provider(self, handler):
        async def record(request):
            self.calls.append(json.loads(request.content)["model"])
            return handler(request)
        return GroqProvider(httpx.MockTransport(record), sleep=lambda delay: asyncio.sleep(0))

    def success(self, text="A clear explanation"):
        return httpx.Response(200, json={"choices": [{"message": {"content": text}, "finish_reason": "stop"}]})

    async def test_fast_success(self):
        result = await self.provider(lambda request: self.success()).complete([])
        self.assertEqual(result.model, settings.GROQ_PRIMARY_MODEL)
        self.assertEqual(len(self.calls), 1)

    async def test_model_not_found_fallback_without_retry(self):
        client = self.provider(lambda request: httpx.Response(404, json={"error": "private-secret"}) if len(self.calls) == 1 else self.success())
        result = await client.complete([])
        self.assertEqual(self.calls, [settings.GROQ_PRIMARY_MODEL, settings.GROQ_FALLBACK_MODEL])
        self.assertEqual(result.model, settings.GROQ_FALLBACK_MODEL)

    async def test_credentials_not_retried_or_exposed(self):
        for status in [401, 403, 400]:
            self.calls.clear()
            with self.assertRaises(AIProviderError) as caught:
                await self.provider(lambda request: httpx.Response(status, text="private-secret")).complete([])
            self.assertNotIn("private-secret", str(caught.exception))
            self.assertEqual(len(self.calls), 1)

    async def test_transient_failures_bounded(self):
        for status in [429, 500, 503]:
            self.calls.clear()
            with self.assertRaises(AIProviderError) as caught:
                await self.provider(lambda request: httpx.Response(status)).complete([])
            self.assertTrue(caught.exception.retryable)
            self.assertEqual(len(self.calls), 4)

    async def test_network_and_timeout(self):
        for failure, kind in [(httpx.ConnectError, "network"), (httpx.ReadTimeout, "timeout")]:
            self.calls.clear()
            def handler(request):
                raise failure("private-secret", request=request)
            with self.assertRaises(AIProviderError) as caught:
                await self.provider(handler).complete([])
            self.assertEqual(caught.exception.kind, kind)
            self.assertEqual(len(self.calls), 4)

    async def test_structured_invalid_schema_escalates(self):
        client = self.provider(lambda request: self.success('{"score": 100}') if len(self.calls) == 1 else self.success('{"score": 8}'))
        grade, model = await client.structured([], Grade)
        self.assertEqual(grade.score, 8)
        self.assertEqual(model, settings.GROQ_FALLBACK_MODEL)

    async def test_malformed_response_fails(self):
        with self.assertRaises(AIProviderError):
            await self.provider(lambda request: httpx.Response(200, json={})).complete([])

    async def test_structured_both_models_invalid(self):
        with self.assertRaises(AIProviderError):
            await self.provider(lambda request: self.success("not json")).structured([], Grade)

    async def test_missing_key_no_simulation(self):
        with patch.object(settings, "GROQ_API_KEY", ""):
            with self.assertRaises(AIProviderError) as caught:
                await self.provider(lambda request: self.success()).complete([])
        self.assertEqual(caught.exception.kind, "not_configured")
        self.assertEqual(self.calls, [])

    async def test_stream_success(self):
        content = 'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\ndata: [DONE]\n\n'
        result = [chunk async for chunk in self.provider(lambda request: httpx.Response(200, text=content)).stream([])]
        self.assertEqual(result, ["Hello"])

    async def test_stream_fallback_before_tokens(self):
        content = 'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\ndata: [DONE]\n\n'
        result = [chunk async for chunk in self.provider(lambda request: httpx.Response(404) if len(self.calls) == 1 else httpx.Response(200, text=content)).stream([])]
        self.assertEqual(result, ["Hello"])
        self.assertEqual(len(self.calls), 2)

    async def test_stream_never_restarts_after_partial_output(self):
        content = 'data: {"choices":[{"delta":{"content":"Partial"}}]}\n\n'
        with self.assertRaises(AIProviderError):
            async for chunk in self.provider(lambda request: httpx.Response(200, text=content)).stream([]):
                self.assertEqual(chunk, "Partial")
        self.assertEqual(len(self.calls), 1)

    async def test_cancellation_propagates(self):
        def handler(request):
            raise asyncio.CancelledError
        with self.assertRaises(asyncio.CancelledError):
            async for chunk in self.provider(handler).stream([]):
                self.fail("Cancellation must not yield a fabricated reply")
