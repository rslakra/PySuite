"""Lock pattern — mutex protects a shared counter; race vs locked."""

from __future__ import annotations

import threading
import time


def increment_unsafe(counter: list[int], iterations: int) -> None:
    for _ in range(iterations):
        value = counter[0]
        time.sleep(0)  # yield — increases chance of lost updates
        counter[0] = value + 1


def increment_safe(counter: list[int], lock: threading.Lock, iterations: int) -> None:
    for _ in range(iterations):
        with lock:
            counter[0] += 1


def run_race() -> int:
    counter = [0]
    threads = [
        threading.Thread(target=increment_unsafe, args=(counter, 500))
        for _ in range(4)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return counter[0]


def run_locked() -> int:
    counter = [0]
    lock = threading.Lock()
    threads = [
        threading.Thread(target=increment_safe, args=(counter, lock, 500))
        for _ in range(4)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return counter[0]


def main() -> None:
    expected = 4 * 500
    unsafe_total = run_race()
    safe_total = run_locked()

    print(f"Expected total: {expected}")
    print(f"Without lock:   {unsafe_total}  (lost updates — race condition)")
    print(f"With lock:      {safe_total}  (correct — mutex serializes critical section)")


if __name__ == "__main__":
    main()
