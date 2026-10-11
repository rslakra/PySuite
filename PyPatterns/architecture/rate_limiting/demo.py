"""Rate Limiting pattern — token bucket limits requests per time window."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class TokenBucket:
    """Classic token bucket: refill rate caps sustained throughput."""

    capacity: float
    refill_rate: float  # tokens per second
    _tokens: float = 0.0
    _last_refill: float = 0.0

    def __post_init__(self) -> None:
        self._tokens = self.capacity
        self._last_refill = time.monotonic()

    def _refill(self, now: float) -> None:
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now

    def allow(self) -> bool:
        now = time.monotonic()
        self._refill(now)
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False


def main() -> None:
    bucket = TokenBucket(capacity=3.0, refill_rate=5.0)
    allowed = rejected = 0

    for i in range(8):
        if bucket.allow():
            allowed += 1
            print(f"  request {i + 1}: allowed")
        else:
            rejected += 1
            print(f"  request {i + 1}: rejected (429)")
        time.sleep(0.05)

    print(f"Token bucket: {allowed} allowed, {rejected} rejected — burst capped at capacity")


if __name__ == "__main__":
    main()
