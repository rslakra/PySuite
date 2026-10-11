"""Balking — single-flight gate: if busy, return immediately without blocking."""

from __future__ import annotations

import threading
import time


class SingleFlightDoor:
    """Only one passenger may pass; others balk (return False) if the door is busy."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._in_use = False

    def enter(self, passenger: str) -> bool:
        with self._lock:
            if self._in_use:
                return False
            self._in_use = True

        print(f"{passenger} entered")
        time.sleep(0.05)
        with self._lock:
            self._in_use = False
        print(f"{passenger} exited")
        return True


def main() -> None:
    door = SingleFlightDoor()
    results: list[tuple[str, bool]] = []

    def attempt(name: str) -> None:
        results.append((name, door.enter(name)))

    threads = [
        threading.Thread(target=attempt, args=("Alice",)),
        threading.Thread(target=attempt, args=("Bob",)),
        threading.Thread(target=attempt, args=("Carol",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for name, entered in sorted(results):
        status = "entered" if entered else "balked (door busy)"
        print(f"{name}: {status}")


if __name__ == "__main__":
    main()
