"""Per-user rate limiting for the expensive extraction endpoints.

Each extraction costs money (Claude) and CPU (Whisper), so we cap how often a
single authenticated user can trigger one — both a short burst limit and a daily
quota. State is kept in memory, which is correct here because the service runs as
a single instance (persistent disk pins it, WEB_CONCURRENCY=1). If the app is ever
scaled to multiple instances, this must move to a shared store (e.g. Redis).

Counters use fixed windows and reset on restart — acceptable for abuse control at
this scale.
"""

import threading
import time

from fastapi import Depends, HTTPException, status

from ..auth import get_current_user_id
from ..config import get_settings


class _FixedWindow:
    """Per-user hit counts within a fixed window of `window_s` seconds."""

    def __init__(self, window_s: int) -> None:
        self._window_s = window_s
        self._counts: dict[str, tuple[int, float]] = {}  # user -> (count, window_start)

    def _current(self, user_id: str, now: float) -> tuple[int, float]:
        count, start = self._counts.get(user_id, (0, now))
        if now - start >= self._window_s:  # window expired -> reset
            return 0, now
        return count, start

    def retry_after(self, user_id: str, limit: int, now: float) -> int | None:
        """Seconds until the window frees up if the user is at the limit, else None."""
        count, start = self._current(user_id, now)
        if count >= limit:
            return int(self._window_s - (now - start)) + 1
        return None

    def commit(self, user_id: str, now: float) -> None:
        count, start = self._current(user_id, now)
        self._counts[user_id] = (count + 1, start)


class UserRateLimiter:
    def __init__(self, per_minute: int, per_day: int) -> None:
        self.per_minute = per_minute
        self.per_day = per_day
        self._lock = threading.Lock()
        self._minute = _FixedWindow(60)
        self._day = _FixedWindow(86_400)

    def check(self, user_id: str) -> None:
        """Raise HTTP 429 (with Retry-After) if over either limit.

        Quota is consumed only when the request is allowed by BOTH windows, so a
        request rejected by one limit doesn't eat into the other.
        """
        now = time.time()
        with self._lock:
            day_retry = self._day.retry_after(user_id, self.per_day, now)
            minute_retry = self._minute.retry_after(user_id, self.per_minute, now)
            if day_retry is None and minute_retry is None:
                self._day.commit(user_id, now)
                self._minute.commit(user_id, now)
                return
            # Report whichever limit was hit (prefer the daily one — it's the
            # harder ceiling and its retry is more informative).
            retry, scope = (
                (day_retry, "daily") if day_retry is not None else (minute_retry, "per-minute")
            )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({scope}). Try again in {retry}s.",
            headers={"Retry-After": str(retry)},
        )


_settings = get_settings()
_limiter = UserRateLimiter(
    per_minute=_settings.extract_rate_per_minute,
    per_day=_settings.extract_rate_per_day,
)


def enforce_extraction_quota(user_id: str = Depends(get_current_user_id)) -> str:
    """FastAPI dependency: authenticate, then rate-limit. Returns the user id.

    Use in place of `get_current_user_id` on the expensive endpoints.
    """
    _limiter.check(user_id)
    return user_id
