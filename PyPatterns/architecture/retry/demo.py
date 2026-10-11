"""Retry pattern — exponential backoff for transient failures."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Retry with exponential backoff and optional jitter."""

    max_attempts: int = 5
    base_delay: float = 0.05
    max_delay: float = 0.5

    def run(self, operation: Callable[[], T]) -> T:
        delay = self.base_delay
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                result = operation()
                print(f"  attempt {attempt}: success")
                return result
            except RuntimeError as exc:
                last_error = exc
                print(f"  attempt {attempt}: {exc}")
                if attempt == self.max_attempts:
                    break
                jitter = random.uniform(0, delay * 0.25)
                sleep_for = min(self.max_delay, delay) + jitter
                time.sleep(sleep_for)
                delay *= 2
        raise RuntimeError(f"exhausted {self.max_attempts} attempts") from last_error


def main() -> None:
    calls = {"n": 0}

    def flaky_fetch() -> str:
        calls["n"] += 1
        if calls["n"] < 4:
            raise RuntimeError("upstream timeout")
        return "payload-OK"

    policy = RetryPolicy(max_attempts=5, base_delay=0.03)
    print(f"Result: {policy.run(flaky_fetch)}")
    print("Transient errors absorbed — backoff prevents thundering herd")


if __name__ == "__main__":
    main()
