"""Request IDs and bounded JSON access events, without query/body/credential values."""
import json
import logging
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger("plant.http")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


async def safe_server_error(request: Request, exc: Exception) -> JSONResponse:
    # The outer ServerErrorMiddleware sends this response outside user middleware.
    headers = {"X-Request-ID": getattr(request.state, "request_id", uuid4().hex),
               "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    origin = request.headers.get("origin")
    if origin in settings.CORS_ORIGINS:
        headers.update({"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Expose-Headers": "X-Request-ID, Retry-After", "Vary": "Origin"})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"}, headers=headers)


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        started = perf_counter()
        status_code = 500

        async def send_with_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)["X-Request-ID"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            route = getattr(scope.get("route"), "path", "unmatched")
            method = scope.get("method", "")
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
                method = "OTHER"
            logger.info(json.dumps({"event": "http_request", "request_id": request_id,
                                    "method": method, "route": route, "status": status_code,
                                    "duration_ms": round((perf_counter() - started) * 1000, 2)}))
