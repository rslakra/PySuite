"""Queue-based load leveling — buffer bursts, drain backend at steady rate."""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    req_id: int
    payload: str


class LoadLevelingQueue:
    """Absorbs traffic spikes; backend worker drains at fixed pace."""

    def __init__(self, backend_delay: float = 0.05) -> None:
        self._queue: queue.Queue[Request | None] = queue.Queue()
        self._backend_delay = backend_delay
        self._processed: list[str] = []

    def submit(self, request: Request) -> None:
        self._queue.put(request)

    def _backend_worker(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                self._queue.task_done()
                break
            time.sleep(self._backend_delay)
            self._processed.append(item.payload)
            self._queue.task_done()

    def run(self, burst: list[Request]) -> list[str]:
        worker = threading.Thread(target=self._backend_worker, daemon=True)
        worker.start()
        for req in burst:
            self.submit(req)
        self._queue.join()
        self._queue.put(None)
        worker.join(timeout=1.0)
        return self._processed


def main() -> None:
    burst = [Request(i, f"job-{i}") for i in range(12)]
    print(f"Burst: {len(burst)} requests arrive instantly")

    leveler = LoadLevelingQueue(backend_delay=0.03)
    start = time.perf_counter()
    results = leveler.run(burst)
    elapsed = time.perf_counter() - start

    print(f"Queue depth peaked at {len(burst)} while backend kept steady pace")
    print(f"Processed {len(results)} jobs in {elapsed:.2f}s (not instant)")
    print(f"Last job: {results[-1]}")


if __name__ == "__main__":
    main()
