"""In-memory sliding-window rate limiting middleware for the demo."""

from collections import deque
from threading import Lock
from time import monotonic

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings


# Shared across middleware instances in this Python process.
_requests: dict[str, deque[float]] = {}
_lock = Lock()
_cleanup_counter = 0
_CLEANUP_INTERVAL = 256


def _prune_expired_requests_locked(now: float, window: float) -> None:
    """Remove expired histories. Caller must hold _lock."""
    cutoff = now - window

    for key, history in list(_requests.items()):
        while history and history[0] <= cutoff:
            history.popleft()

        if not history:
            _requests.pop(key, None)


def reset_rate_limit_state() -> None:
    """Clear request history, primarily to isolate automated tests."""
    global _cleanup_counter

    with _lock:
        _requests.clear()
        _cleanup_counter = 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply an IP-based sliding-window request limit."""

    async def dispatch(self, request: Request, call_next):
        # Health checks must remain available for monitoring.
        if request.url.path == "/health":
            return await call_next(request)

        settings = get_settings()

        # Do not trust a client-supplied patient ID as the rate-limit key.
        client_ip = (
            request.client.host
            if request.client is not None
            else "anonymous"
        )
        key = f"ip:{client_ip}"

        now = monotonic()
        window = settings.rate_limit_window_ms / 1000
        limit = settings.rate_limit_max_requests

        global _cleanup_counter

        with _lock:
            _cleanup_counter += 1

            # Periodically remove stale histories for inactive client IPs.
            if _cleanup_counter >= _CLEANUP_INTERVAL:
                _prune_expired_requests_locked(now, window)
                _cleanup_counter = 0

            history = _requests.setdefault(key, deque())

            while history and history[0] <= now - window:
                history.popleft()

            if limit == 0 or len(history) >= limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            "Too many requests. Please try again shortly."
                        )
                    },
                    headers={
                        "Retry-After": str(max(1, int(window)))
                    },
                )

            history.append(now)

        return await call_next(request)
