import asyncio
import json
import logging
import time
from dataclasses import dataclass

import httpx
from pydantic import ValidationError

from backend.config import settings

logger = logging.getLogger(__name__)
API_URL = "https://api.groq.com/openai/v1"


class AIProviderError(Exception):
    def __init__(self, kind, message, retryable=False):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.retryable = retryable

    def public(self):
        return {"code": self.kind, "message": self.message, "retryable": self.retryable}


@dataclass
class Completion:
    text: str
    model: str


def classify_error(status_code):
    if status_code in (401, 403):
        return AIProviderError("authentication", "The assistant cannot connect. Please contact the platform administrator.")
    if status_code == 404:
        return AIProviderError("model_unavailable", "The configured AI model is unavailable. Please contact the platform administrator.", True)
    if status_code == 429:
        return AIProviderError("rate_limit", "The assistant is busy. Please wait a moment and retry.", True)
    if status_code >= 500:
        return AIProviderError("service", "The assistant is temporarily unavailable. Please retry shortly.", True)
    return AIProviderError("invalid_request", "The assistant could not process this request. Try a shorter question.")


def malformed_error():
    return AIProviderError("invalid_response", "The assistant returned an incomplete response. Please retry.", True)


class GroqProvider:
    def __init__(self, transport=None, sleep=asyncio.sleep):
        self.transport = transport
        self.sleep = sleep

    def _client(self):
        return httpx.AsyncClient(transport=self.transport, timeout=httpx.Timeout(settings.GROQ_TIMEOUT_SECONDS, connect=8.0))

    def _models(self, model=None):
        initial = model or settings.GROQ_PRIMARY_MODEL
        alternate = settings.GROQ_PRIMARY_MODEL if initial == settings.GROQ_FALLBACK_MODEL else settings.GROQ_FALLBACK_MODEL
        return list(dict.fromkeys([initial, alternate]))

    def _headers(self):
        if not settings.GROQ_API_KEY:
            raise AIProviderError("not_configured", "The assistant is unavailable until the administrator configures AI access.")
        return {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}

    def _body(self, messages, model, stream=False, structured=False):
        body = {"model": model, "messages": messages, "temperature": 0.4, "stream": stream, "max_completion_tokens": settings.GROQ_MAX_TOKENS}
        if model.startswith("openai/gpt-oss-"):
            body.update({"reasoning_effort": "low", "include_reasoning": False})
        if structured:
            body["response_format"] = {"type": "json_object"}
        return body

    def _record(self, model, started, error=None):
        logger.info("ai_request %s", json.dumps({"model": model, "latency_ms": round((time.monotonic() - started) * 1000), "error_kind": error.kind if error else None}))

    async def _request(self, messages, model, structured=False):
        headers = self._headers()
        for attempt in range(settings.GROQ_MAX_RETRIES + 1):
            started = time.monotonic()
            error = None
            try:
                async with self._client() as client:
                    response = await client.post(f"{API_URL}/chat/completions", headers=headers, json=self._body(messages, model, structured=structured))
                if response.status_code != 200:
                    raise classify_error(response.status_code)
                try:
                    payload = response.json()
                    content = payload["choices"][0]["message"]["content"]
                    if not isinstance(content, str) or not content.strip():
                        raise ValueError
                    if payload["choices"][0].get("finish_reason") == "length":
                        raise ValueError
                except (ValueError, KeyError, IndexError, TypeError):
                    raise malformed_error() from None
                self._record(model, started)
                return Completion(content, model)
            except httpx.TimeoutException:
                error = AIProviderError("timeout", "The assistant took too long to respond. Please retry.", True)
            except httpx.RequestError:
                error = AIProviderError("network", "The assistant connection was interrupted. Please retry.", True)
            except AIProviderError as failure:
                error = failure
            self._record(model, started, error)
            if error.kind not in {"rate_limit", "service", "timeout", "network"} or attempt == settings.GROQ_MAX_RETRIES:
                raise error
            await self.sleep(min(0.5 * 2 ** attempt, 2.0))

    async def complete(self, messages, model=None, structured=False):
        for candidate in self._models(model):
            try:
                return await self._request(messages, candidate, structured)
            except AIProviderError as error:
                if not error.retryable:
                    raise
                last_error = error
        raise last_error

    async def structured(self, messages, schema, model=None):
        for candidate in self._models(model):
            try:
                completion = await self._request(messages, candidate, True)
                value = schema.model_validate_json(completion.text)
                return value, completion.model
            except ValidationError:
                last_error = malformed_error()
            except AIProviderError as error:
                if not error.retryable:
                    raise
                last_error = error
        raise last_error

    async def stream(self, messages, model=None):
        headers = self._headers()
        for candidate in self._models(model):
            for attempt in range(settings.GROQ_MAX_RETRIES + 1):
                started = time.monotonic()
                emitted = False
                error = None
                try:
                    async with self._client() as client:
                        async with client.stream("POST", f"{API_URL}/chat/completions", headers=headers, json=self._body(messages, candidate, stream=True)) as response:
                            if response.status_code != 200:
                                await response.aread()
                                raise classify_error(response.status_code)
                            async for line in response.aiter_lines():
                                if not line.startswith("data:"):
                                    continue
                                data = line[5:].strip()
                                if data == "[DONE]":
                                    if not emitted:
                                        raise malformed_error()
                                    self._record(candidate, started)
                                    return
                                try:
                                    event = json.loads(data)
                                    choices = event.get("choices", [])
                                    if not choices:
                                        continue
                                    if choices[0].get("finish_reason") == "length":
                                        raise malformed_error()
                                    content = choices[0].get("delta", {}).get("content", "")
                                    if not isinstance(content, str):
                                        raise ValueError
                                except (ValueError, TypeError, AttributeError, IndexError):
                                    raise malformed_error() from None
                                if content:
                                    emitted = True
                                    yield content
                            raise malformed_error()
                except httpx.TimeoutException:
                    error = AIProviderError("timeout", "The assistant took too long to respond. Please retry.", True)
                except httpx.RequestError:
                    error = AIProviderError("network", "The assistant connection was interrupted. Please retry.", True)
                except AIProviderError as failure:
                    error = failure
                self._record(candidate, started, error)
                if emitted or not error.retryable:
                    raise error
                last_error = error
                if error.kind not in {"rate_limit", "service", "timeout", "network"} or attempt == settings.GROQ_MAX_RETRIES:
                    break
                await self.sleep(min(0.5 * 2 ** attempt, 2.0))
        raise last_error

    async def available_models(self):
        async with self._client() as client:
            response = await client.get(f"{API_URL}/models", headers=self._headers())
        if response.status_code != 200:
            raise classify_error(response.status_code)
        return {item["id"] for item in response.json()["data"]}


provider = GroqProvider()
