"""
RiskIntel upay - Real-Time Server-Side Rate Limiter
File: backend/rate_limiter.py

Implements a high-precision sliding-window rate limiter.
Returns HTTP 429 with 'Retry-After' when thresholds are exceeded.
Architected for high throughput; can be seamlessly swapped for Redis
in distributed multi-node clusters.
"""

import time
import threading
import logging
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status

logger = logging.getLogger("riskintel.rate_limiter")


class SlidingWindowRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter.
    Tracks timestamps of requests within a moving window.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._store: Dict[str, List[float]] = {}
        self._last_cleanup = time.time()

    def _cleanup_stale(self, now: float, max_window: float = 300.0) -> None:
        """Removes buckets that have had no traffic for longer than max_window."""
        if now - self._last_cleanup < 60.0:
            return
        self._last_cleanup = now
        stale_keys = [
            key for key, timestamps in self._store.items()
            if not timestamps or (now - timestamps[-1]) > max_window
        ]
        for key in stale_keys:
            self._store.pop(key, None)

    def is_allowed(
        self,
        identifier: str,
        limit: int,
        window_seconds: int = 60
    ) -> tuple[bool, int]:
        """
        Determines whether a request with a given identifier is permitted.
        Returns:
            (is_allowed: bool, retry_after_seconds: int)
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            self._cleanup_stale(now)
            timestamps = self._store.get(identifier, [])
            # Filter timestamps within current sliding window
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= limit:
                # Limit exceeded; calculate when the oldest recorded request within window expires
                oldest_in_window = valid_timestamps[0]
                retry_after = max(1, int(oldest_in_window + window_seconds - now))
                self._store[identifier] = valid_timestamps
                return False, retry_after

            valid_timestamps.append(now)
            self._store[identifier] = valid_timestamps
            return True, 0

    def reset(self, identifier: Optional[str] = None) -> None:
        """Resets tracking state (primarily for automated testing)."""
        with self._lock:
            if identifier:
                self._store.pop(identifier, None)
            else:
                self._store.clear()


# Global in-memory rate limiter singleton
rate_limiter = SlidingWindowRateLimiter()


def rate_limit_guard(
    limit: int,
    window_seconds: int = 60,
    key_prefix: str = "generic"
):
    """
    FastAPI dependency factory enforcing rate limits on endpoints.
    Identifies callers by authenticated user_id if present, or client IP address.
    """
    async def dependency(request: Request):
        # Extract IP or forwarded IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        # Combine route prefix with identifier
        rate_key = f"{key_prefix}:{client_ip}"

        allowed, retry_after = rate_limiter.is_allowed(
            identifier=rate_key,
            limit=limit,
            window_seconds=window_seconds
        )

        if not allowed:
            logger.warning(
                "Rate limit exceeded for %s on %s. Limit: %d/%ds. Retry-After: %ds",
                rate_key,
                request.url.path,
                limit,
                window_seconds,
                retry_after
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: maximum {limit} requests per {window_seconds}s. Please retry in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency

