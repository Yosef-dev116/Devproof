import time
from collections import defaultdict

from fastapi import HTTPException

WINDOW_SECONDS = 3600
_calls: dict[tuple[str, int], list[float]] = defaultdict(list)


def enforce_rate_limit(bucket: str, user_id: int, limit: int) -> None:
    key = (bucket, user_id)
    now = time.monotonic()
    recent = [call_time for call_time in _calls[key] if now - call_time < WINDOW_SECONDS]
    if len(recent) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"rate limit reached ({limit} per hour) - please try again later",
        )
    recent.append(now)
    _calls[key] = recent
