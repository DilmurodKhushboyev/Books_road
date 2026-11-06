"""Oddiy sliding-window rate limiter (jarayon xotirasida).

Bitta instans uchun yetarli. Bir nechta instansga o'tilganda shu interfeysni saqlab,
ichini Redis bilan almashtirish kifoya (chaqiruvchilar o'zgarmaydi).
"""
import time
from collections import deque

from app.constants import RATE_AI_PER_MIN, RATE_GENERAL_PER_MIN

_WINDOW_SECONDS = 60.0
_CLEANUP_THRESHOLD = 10_000


class RateLimiter:
    def __init__(self, limit: int, window: float = _WINDOW_SECONDS) -> None:
        self._limit = limit
        self._window = window
        self._hits: dict[int, deque[float]] = {}

    def allow(self, key: int, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] >= self._window:
            hits.popleft()
        if len(hits) >= self._limit:
            return False
        hits.append(now)
        if len(self._hits) > _CLEANUP_THRESHOLD:
            self._cleanup(now)
        return True

    def _cleanup(self, now: float) -> None:
        stale = [key for key, hits in self._hits.items() if not hits or now - hits[-1] >= self._window]
        for key in stale:
            del self._hits[key]


general_limiter = RateLimiter(RATE_GENERAL_PER_MIN)
ai_limiter = RateLimiter(RATE_AI_PER_MIN)
