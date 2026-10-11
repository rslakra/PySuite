"""Competing consumers — multiple workers race for messages on one queue."""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    job_id: int
    task: str


class WorkQueue:
    """Shared queue; whichever consumer is idle grabs the next job."""

    def __init__(self) -> None:
        self._queue: queue.Queue[Job | None] = queue.Queue()
        self._assignments: list[str] = []

    def enqueue(self, job: Job) -> None:
        self._queue.put(job)

    def _consumer(self, name: str) -> None:
        while True:
            job = self._queue.get()
            if job is None:
                self._queue.task_done()
                break
            time.sleep(0.02)
            self._assignments.append(f"{name} ← {job.task}")
            self._queue.task_done()

    def run(self, jobs: list[Job], consumers: int = 3) -> list[str]:
        workers = [
            threading.Thread(target=self._consumer, args=(f"consumer-{i}",), daemon=True)
            for i in range(consumers)
        ]
        for worker in workers:
            worker.start()
        for job in jobs:
            self.enqueue(job)
        self._queue.join()
        for _ in workers:
            self._queue.put(None)
        for worker in workers:
            worker.join(timeout=1.0)
        return self._assignments


def main() -> None:
    jobs = [Job(i, f"task-{i}") for i in range(9)]
    queue_demo = WorkQueue()

    print(f"Enqueuing {len(jobs)} jobs for 3 competing consumers...")
    assignments = queue_demo.run(jobs, consumers=3)
    for line in sorted(assignments, key=lambda s: s.split("←")[1].strip()):
        print(f"  {line}")
    print("Work spreads across consumers — add more workers to scale throughput")


if __name__ == "__main__":
    main()
