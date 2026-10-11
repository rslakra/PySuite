"""Atomic operation — concurrent increment; unsafe vs Lock-protected updates."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass
class Counter:
    value: int = 0


def increment_unsafe(counter: Counter, steps: int) -> None:
    """Non-atomic read-modify-write — GIL can switch between read and write."""
    for _ in range(steps):
        current = counter.value
        time.sleep(0)  # yield GIL so another thread can observe the same current
        counter.value = current + 1


def increment_safe(counter: Counter, lock: threading.Lock, steps: int) -> None:
    for _ in range(steps):
        with lock:
            current = counter.value
            time.sleep(0)
            counter.value = current + 1


def run_trial(
    label: str,
    *,
    safe: bool,
    threads: int = 8,
    steps_per_thread: int = 2_000,
) -> None:
    counter = Counter()
    lock = threading.Lock()
    group = [
        threading.Thread(
            target=increment_safe if safe else increment_unsafe,
            args=(counter, lock, steps_per_thread) if safe else (counter, steps_per_thread),
            daemon=True,
        )
        for _ in range(threads)
    ]
    for t in group:
        t.start()
    for t in group:
        t.join()

    expected = threads * steps_per_thread
    print(f"{label}: counter={counter.value} expected={expected} ok={counter.value == expected}")


def main() -> None:
    print(
        "CPython's GIL limits parallel bytecode execution, but read-modify-write "
        "still races when the interpreter switches threads between opcodes."
    )
    print("Running concurrent increments (8 threads × 2_000 steps each)...")
    run_trial("Unsafe (read / yield / write)", safe=False)
    run_trial("Safe   (Lock wraps RMW)      ", safe=True)
    print("Use threading.Lock (or queue-based ownership) when correctness matters.")


if __name__ == "__main__":
    main()
