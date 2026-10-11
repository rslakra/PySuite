"""Scheduler pattern — serialize job execution through a single worker gate."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from queue import Empty, Queue


@dataclass(order=True)
class Job:
    priority: int
    name: str = field(compare=False)
    action: Callable[[], str] = field(compare=False)


class Scheduler:
    """One worker thread drains a priority queue — jobs never overlap."""

    def __init__(self) -> None:
        self._queue: Queue[Job] = Queue()
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def submit(self, name: str, action: Callable[[], str], priority: int = 5) -> None:
        self._queue.put(Job(priority, name, action))

    def _drain(self, pending: list[Job]) -> None:
        while True:
            try:
                pending.append(self._queue.get_nowait())
            except Empty:
                return

    def _run(self) -> None:
        pending: list[Job] = []
        while not self._stop.is_set() or pending or not self._queue.empty():
            self._drain(pending)
            if not pending:
                try:
                    pending.append(self._queue.get(timeout=0.05))
                except Empty:
                    continue
            pending.sort()
            job = pending.pop(0)
            print(f"[Scheduler] start  {job.name} (priority {job.priority})")
            result = job.action()
            print(f"[Scheduler] finish {job.name} → {result}")

    def shutdown(self) -> None:
        self._stop.set()
        self._worker.join(timeout=2.0)


def main() -> None:
    scheduler = Scheduler()

    def backup() -> str:
        time.sleep(0.08)
        return "snapshot saved"

    def report() -> str:
        time.sleep(0.05)
        return "metrics exported"

    def cleanup() -> str:
        time.sleep(0.04)
        return "temp files removed"

    scheduler.submit("backup", backup, priority=1)
    scheduler.submit("report", report, priority=3)
    scheduler.submit("cleanup", cleanup, priority=2)

    time.sleep(0.5)
    scheduler.shutdown()
    print("All jobs ran one-at-a-time through the scheduler gate")


if __name__ == "__main__":
    main()
