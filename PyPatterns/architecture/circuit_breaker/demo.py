"""Circuit breaker — fail fast when downstream errors exceed a threshold."""

from __future__ import annotations

import enum
import random
import time
from collections.abc import Callable
from dataclasses import dataclass


class State(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout: float = 0.15
    failures: int = 0
    state: State = State.CLOSED
    _opened_at: float = 0.0

    def call(self, operation: Callable[[], str]) -> str:
        if self.state is State.OPEN:
            if time.monotonic() - self._opened_at >= self.recovery_timeout:
                self.state = State.HALF_OPEN
                print("  breaker → HALF-OPEN (probe allowed)")
            else:
                raise RuntimeError("circuit OPEN — call rejected")

        try:
            result = operation()
        except RuntimeError:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.state = State.OPEN
                self._opened_at = time.monotonic()
                print(f"  breaker → OPEN after {self.failures} failures")
            raise

        self.failures = 0
        if self.state is State.HALF_OPEN:
            self.state = State.CLOSED
            print("  breaker → CLOSED (probe succeeded)")
        return result


class FlakyPaymentGateway:
    """Simulated downstream that fails most of the time."""

    def __init__(self) -> None:
        random.seed(7)

    def charge(self) -> str:
        if random.random() < 0.7:
            raise RuntimeError("gateway timeout")
        return "payment accepted"


def main() -> None:
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0.12)
    gateway = FlakyPaymentGateway()

    print("Calling flaky gateway through circuit breaker...")
    for attempt in range(8):
        try:
            msg = breaker.call(gateway.charge)
            print(f"  attempt {attempt + 1}: {msg} [{breaker.state.value}]")
        except RuntimeError as exc:
            print(f"  attempt {attempt + 1}: {exc} [{breaker.state.value}]")
        time.sleep(0.04)


if __name__ == "__main__":
    main()
