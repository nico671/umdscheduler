import math
import time
from threading import Lock
from typing import Dict, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class InMemoryFixedWindowLimiter:
    def __init__(self, *, limit: int, window_seconds: int, burst: int = 0):
        self.limit = limit
        self.window_seconds = window_seconds
        self.capacity = limit + max(0, burst)
        self._lock = Lock()
        self._windows: Dict[str, Tuple[float, int]] = {}

    def consume(self, key: str) -> Tuple[bool, int, int, int]:
        now = time.monotonic()

        with self._lock:
            window_start, count = self._windows.get(key, (now, 0))

            if now - window_start >= self.window_seconds:
                window_start = now
                count = 0

            if count >= self.capacity:
                retry_after = max(
                    1,
                    int(math.ceil(self.window_seconds - (now - window_start))),
                )
                self._windows[key] = (window_start, count)
                return False, self.capacity, 0, retry_after

            count += 1
            self._windows[key] = (window_start, count)
            remaining = max(0, self.capacity - count)
            return True, self.capacity, remaining, 0


def _resolve_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        parts = [part.strip() for part in forwarded_for.split(",")]
        if parts and parts[0]:
            return parts[0]

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def _rate_limit_headers(limit: int, remaining: int) -> Dict[str, str]:
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
    }


def _too_many_requests_response(limit: int, retry_after: int) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."},
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": "0",
        },
    )


class APIBudgetMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        global_limiter: InMemoryFixedWindowLimiter,
        schedule_limiter: InMemoryFixedWindowLimiter,
        schedule_path: str = "/api/v1/schedules",
    ):
        super().__init__(app)
        self.global_limiter = global_limiter
        self.schedule_limiter = schedule_limiter
        self.schedule_path = schedule_path

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = _resolve_client_ip(request)

        allowed, limit, remaining, retry_after = self.global_limiter.consume(client_ip)
        if not allowed:
            return _too_many_requests_response(limit, retry_after)

        headers = _rate_limit_headers(limit, remaining)

        if (
            request.method.upper() == "POST"
            and request.url.path.rstrip("/") == self.schedule_path
        ):
            allowed, limit, remaining, retry_after = self.schedule_limiter.consume(
                client_ip
            )
            if not allowed:
                return _too_many_requests_response(limit, retry_after)

            headers = _rate_limit_headers(limit, remaining)

        response = await call_next(request)
        for key, value in headers.items():
            response.headers[key] = value

        return response


class ScheduleBodySizeGuardMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, app, *, max_body_bytes: int, schedule_path: str = "/api/v1/schedules"
    ):
        super().__init__(app)
        self.max_body_bytes = max_body_bytes
        self.schedule_path = schedule_path

    async def dispatch(self, request: Request, call_next) -> Response:
        if (
            request.method.upper() == "POST"
            and request.url.path.rstrip("/") == self.schedule_path
        ):
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > self.max_body_bytes:
                        return JSONResponse(
                            status_code=413,
                            content={
                                "detail": "Request body too large for schedule generation payload."
                            },
                        )
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid Content-Length header."},
                    )
            else:
                body = await request.body()
                if len(body) > self.max_body_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Request body too large for schedule generation payload."
                        },
                    )

        return await call_next(request)
