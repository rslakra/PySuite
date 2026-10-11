"""Saga pattern — distributed steps with compensation on failure."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


Step = tuple[str, Callable[[], None], Callable[[], None]]


@dataclass
class SagaOrchestrator:
    """Run steps in order; compensate completed steps if any step fails."""

    steps: list[Step] = field(default_factory=list)
    _completed: list[tuple[str, Callable[[], None]]] = field(default_factory=list)

    def add(self, name: str, execute: Callable[[], None], compensate: Callable[[], None]) -> None:
        self.steps.append((name, execute, compensate))

    def run(self) -> None:
        for name, execute, compensate in self.steps:
            try:
                execute()
                self._completed.append((name, compensate))
                print(f"  step ok: {name}")
            except RuntimeError as exc:
                print(f"  step failed: {name} ({exc})")
                self._rollback()
                raise
        print("Saga completed — all steps committed")

    def _rollback(self) -> None:
        print("  compensating...")
        while self._completed:
            name, compensate = self._completed.pop()
            compensate()
            print(f"  compensated: {name}")


def main() -> None:
    state = {"hotel": False, "flight": False, "payment": False}

    def book_hotel() -> None:
        state["hotel"] = True
        print("    booked hotel")

    def cancel_hotel() -> None:
        state["hotel"] = False
        print("    cancelled hotel")

    def book_flight() -> None:
        raise RuntimeError("no seats")

    def cancel_flight() -> None:
        state["flight"] = False

    def capture_payment() -> None:
        state["payment"] = True
        print("    captured payment")

    def refund_payment() -> None:
        state["payment"] = False
        print("    refunded payment")

    saga = SagaOrchestrator()
    saga.add("reserve-hotel", book_hotel, cancel_hotel)
    saga.add("reserve-flight", book_flight, cancel_flight)
    saga.add("capture-payment", capture_payment, refund_payment)

    try:
        saga.run()
    except RuntimeError:
        print(f"Final state: {state}")
        print("Partial work undone via compensating transactions")


if __name__ == "__main__":
    main()
