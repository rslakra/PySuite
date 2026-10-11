"""Throttling pattern — limit concurrency to protect a fragile backend."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from queue import Queue


@dataclass
class ThrottledBackend:
    """Simulated backend that fails under too many concurrent callers."""

    max_safe: int = 2
    _active: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def handle(self, request_id: int) -> str:
        with self._lock:
            self._active += 1
            overloaded = self._active > self.max_safe
        try:
            time.sleep(0.05)
            if overloaded:
                raise RuntimeError("backend overloaded")
            return f"ok #{request_id}"
        finally:
            with self._lock:
                self._active -= 1


@dataclass
class ThrottleGate:
    """Admission control: only `max_inflight` requests hit the backend at once."""

    max_inflight: int
    _semaphore: threading.Semaphore = field(init=False)

    def __post_init__(self) -> None:
        self._semaphore = threading.Semaphore(self.max_inflight)

    def invoke(self, backend: ThrottledBackend, request_id: int) -> str:
        with self._semaphore:
            return backend.handle(request_id)


def _burst(backend: ThrottledBackend, gate: ThrottleGate | None, n: int) -> list[str]:
    results: Queue[str] = Queue()

    def task(rid: int) -> None:
        try:
            if gate is None:
                results.put(backend.handle(rid))
            else:
                results.put(gate.invoke(backend, rid))
        except RuntimeError as exc:
            results.put(f"fail #{rid}: {exc}")

    with ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(task, i) for i in range(n)]
        for f in as_completed(futures):
            f.result()

    out: list[str] = []
    while not results.empty():
        out.append(results.get())
    return sorted(out)


def main() -> None:
    backend = ThrottledBackend(max_safe=2)
    print("Without throttle (6 concurrent):")
    for line in _burst(backend, None, 6):
        print(f"  {line}")

    print("With throttle (max 2 inflight):")
    gate = ThrottleGate(max_inflight=2)
    for line in _burst(backend, gate, 6):
        print(f"  {line}")

    print("Throttling sheds load at the edge — backend stays within safe capacity")


if __name__ == "__main__":
    main()
