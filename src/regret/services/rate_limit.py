"""In-process abuse limits for authentication endpoints.

Does not persist across process restarts. Does not store passwords.
Email keys are normalized; values are counters only.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from regret.config import get_settings


@dataclass
class LimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: dict[str, list[float]] = {}

    def reset(self) -> None:
        with self._lock:
            self._events.clear()

    def peek(self, key: str, *, limit: int, window_seconds: int) -> LimitDecision:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            stamps = [ts for ts in self._events.get(key, []) if ts >= cutoff]
            self._events[key] = stamps
            if len(stamps) >= limit:
                oldest = stamps[0]
                retry = max(1, int(window_seconds - (now - oldest)) + 1)
                return LimitDecision(allowed=False, retry_after_seconds=retry)
            return LimitDecision(allowed=True)

    def record(self, key: str, *, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            stamps = [ts for ts in self._events.get(key, []) if ts >= cutoff]
            stamps.append(now)
            self._events[key] = stamps

    def clear_prefix(self, prefix: str) -> None:
        with self._lock:
            for key in [k for k in self._events if k.startswith(prefix)]:
                del self._events[key]


limiter = SlidingWindowLimiter()


def login_allowed(*, email: str, ip: str) -> LimitDecision:
    settings = get_settings()
    email_key = f"login:email:{email.strip().lower()}"
    ip_key = f"login:ip:{ip}"
    email_hit = limiter.peek(
        email_key,
        limit=settings.regret_login_fail_limit_email,
        window_seconds=settings.regret_login_window_seconds,
    )
    if not email_hit.allowed:
        return email_hit
    return limiter.peek(
        ip_key,
        limit=settings.regret_login_fail_limit_ip,
        window_seconds=settings.regret_login_window_seconds,
    )


def record_login_failure(*, email: str, ip: str) -> None:
    settings = get_settings()
    limiter.record(f"login:email:{email.strip().lower()}", window_seconds=settings.regret_login_window_seconds)
    limiter.record(f"login:ip:{ip}", window_seconds=settings.regret_login_window_seconds)


def register_allowed(*, ip: str) -> LimitDecision:
    settings = get_settings()
    return limiter.peek(
        f"register:ip:{ip}",
        limit=settings.regret_register_limit_ip,
        window_seconds=settings.regret_register_window_seconds,
    )


def record_registration(*, ip: str) -> None:
    settings = get_settings()
    limiter.record(f"register:ip:{ip}", window_seconds=settings.regret_register_window_seconds)


def clear_login_failures(*, email: str) -> None:
    limiter.clear_prefix(f"login:email:{email.strip().lower()}")
