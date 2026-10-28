import time
import uuid
import logging
from time import perf_counter
from collections import OrderedDict, deque

from starlette.responses import JSONResponse

from backend.config import settings


class SafetyMiddleware:
    def __init__(self, app):
        self.app = app
        self.windows = OrderedDict()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        method = scope.get("method", "GET")
        path = scope.get("path", "/")
        started = perf_counter()
        response_status = 500

        async def secure_send(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = list(message.get("headers", []))
                response_headers.extend([
                    (b"x-content-type-options", b"nosniff"), (b"referrer-policy", b"no-referrer"),
                    (b"x-frame-options", b"DENY"), (b"x-request-id", request_id),
                    (b"permissions-policy", b"camera=(self), microphone=(self), geolocation=()"),
                ])
                private = b"authorization" in headers or path.startswith(("/auth/", "/ai/", "/resume/", "/mock-interview/", "/progress/", "/learning/", "/workspace/", "/activity/", "/analytics/"))
                if private:
                    response_headers = [(key, value) for key, value in response_headers if key.lower() != b"cache-control"]
                    response_headers.append((b"cache-control", b"no-store"))
                elif not any(key.lower() == b"cache-control" for key, value in response_headers):
                    response_headers.append((b"cache-control", b"no-cache"))
                message = {**message, "headers": response_headers}
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False) and not path.startswith(("/static/", "/health/")):
                route = getattr(scope.get("route"), "path", "unmatched")
                logging.getLogger("uvicorn.error").info(
                    "request_id=%s method=%s route=%s status=%d duration_ms=%d",
                    request_id.decode("ascii"), method, route, response_status, (perf_counter() - started) * 1000,
                )

        request_id = uuid.uuid4().hex.encode("ascii")
        write = method in {"POST", "PATCH", "PUT", "DELETE"}
        if write:
            origin = headers.get(b"origin", b"").decode("latin-1")
            if origin and origin not in settings.ALLOWED_ORIGINS:
                return await JSONResponse({"detail": "Request origin is not allowed."}, status_code=403)(scope, receive, secure_send)
        limited_write = write and path.startswith(("/auth/", "/ai/", "/resume/", "/mock-interview/", "/practice/", "/learning/"))
        limited_read = method == "GET" and path in {"/catalog/search", "/workspace/overview"}
        if limited_write or limited_read:
            now = time.monotonic()
            client = (scope.get("client") or ("unknown",))[0]
            group = "auth" if path.startswith("/auth/") else "read" if limited_read else "api"
            key = (client, group)
            window = self.windows.setdefault(key, deque())
            self.windows.move_to_end(key)
            while window and now - window[0] >= 60:
                window.popleft()
            limit = settings.AUTH_RATE_LIMIT if group == "auth" else settings.API_RATE_LIMIT
            if len(window) >= limit:
                return await JSONResponse({"detail": "Too many requests. Please wait a minute and retry."}, status_code=429, headers={"Retry-After": "60"})(scope, receive, secure_send)
            window.append(now)
            if len(self.windows) > 10000:
                self.windows.popitem(last=False)

        await self.app(scope, receive, secure_send)
