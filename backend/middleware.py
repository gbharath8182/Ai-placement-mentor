import time
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
        if method in {"POST", "PATCH", "PUT", "DELETE"}:
            origin = headers.get(b"origin", b"").decode("latin-1")
            if origin and origin not in settings.ALLOWED_ORIGINS:
                return await JSONResponse({"detail": "Request origin is not allowed."}, status_code=403)(scope, receive, send)
            if path.startswith(("/auth/", "/ai/", "/resume/", "/mock-interview/", "/practice/", "/learning/")):
                now = time.monotonic()
                client = (scope.get("client") or ("unknown",))[0]
                group = "auth" if path.startswith("/auth/") else "api"
                key = (client, group)
                window = self.windows.setdefault(key, deque())
                self.windows.move_to_end(key)
                while window and now - window[0] >= 60:
                    window.popleft()
                limit = settings.AUTH_RATE_LIMIT if group == "auth" else settings.API_RATE_LIMIT
                if len(window) >= limit:
                    return await JSONResponse({"detail": "Too many requests. Please wait a minute and retry."}, status_code=429, headers={"Retry-After": "60"})(scope, receive, send)
                window.append(now)
                if len(self.windows) > 10000:
                    self.windows.popitem(last=False)

        async def secure_send(message):
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.extend([(b"x-content-type-options", b"nosniff"), (b"referrer-policy", b"no-referrer"), (b"x-frame-options", b"DENY")])
                if path.startswith(("/auth/", "/ai/", "/resume/", "/mock-interview/", "/progress/", "/learning/")):
                    response_headers.append((b"cache-control", b"no-store"))
                message = {**message, "headers": response_headers}
            await send(message)

        await self.app(scope, receive, secure_send)
