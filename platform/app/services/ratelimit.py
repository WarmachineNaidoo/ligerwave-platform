import time
from typing import Dict, List, Optional
from starlette.requests import Request
from starlette.responses import Response


def _get_client_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For header (reverse proxy support)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RateLimiter:
    """Per-endpoint rate limiter with configurable limits per route pattern."""

    def __init__(self):
        self._windows: Dict[str, List[float]] = {}
        self._limits: Dict[str, int] = {}

    def set_limit(self, path_prefix: str, max_requests: int, window_seconds: int = 60):
        self._limits[path_prefix] = max_requests
        self._windows[f"{path_prefix}:window"] = [0.0] * window_seconds  # track separately

    def get_limit(self, path: str) -> Optional[int]:
        for prefix, limit in sorted(self._limits.items(), key=lambda x: -len(x[0])):
            if path.startswith(prefix):
                return limit
        return None

    def check(self, request: Request) -> Optional[Response]:
        client_ip = _get_client_ip(request)
        path = request.url.path
        now = time.time()

        limit = self.get_limit(path)
        if limit is None:
            return None

        key = f"{client_ip}:{path}"
        window = self._windows.get(key, [])
        window = [t for t in window if now - t < 60]
        if len(window) >= limit:
            return Response(status_code=429, content="rate_limit_exceeded", headers={"Retry-After": "60"})
        window.append(now)
        self._windows[key] = window
        return None


limiter = RateLimiter()
