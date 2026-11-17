"""Small in-memory sliding-window rate limiter (single-process; use Redis in prod)."""
import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request
from app.config import get_settings

_hits: dict[str, deque] = defaultdict(deque)


def check_rate_limit(request: Request) -> None:
    limit = get_settings().rate_limit_per_minute
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    q = _hits[key]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(429, "Too many requests. Please slow down.")
    q.append(now)
