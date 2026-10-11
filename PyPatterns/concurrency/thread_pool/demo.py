"""Thread pool — fixed worker pool processing a shared task queue."""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    task_id: int
    payload: str


class ThreadPool:
    """Fixed number of workers pull tasks from a queue until shutdown."""

    def __init__(self, workers: int) -> None:
        self._tasks: queue.Queue[Task | None] = queue.Queue()
        self._workers = [
            threading.Thread(target=self._worker, name=f"worker-{i}", daemon=True)
            for i in range(workers)
        ]

    def _worker(self) -> None:
        name = threading.current_thread().name
        while True:
            task = self._tasks.get()
            if task is None:
                self._tasks.task_done()
                break
            print(f"[{name}] processing task {task.task_id}: {task.payload}")
            time.sleep(0.02)
            print(f"[{name}] finished task {task.task_id}")
            self._tasks.task_done()

    def start(self) -> None:
        for worker in self._workers:
            worker.start()

    def submit(self, task: Task) -> None:
        self._tasks.put(task)

    def shutdown(self, wait: bool = True) -> None:
        for _ in self._workers:
            self._tasks.put(None)
        if wait:
            for worker in self._workers:
                worker.join()
            self._tasks.join()


def main() -> None:
    pool = ThreadPool(workers=3)
    pool.start()

    print("Submitting 8 tasks to a 3-worker pool...")
    for i in range(8):
        pool.submit(Task(i, f"payload-{i}"))

    pool.shutdown()
    print("All tasks completed by the worker pool")


if __name__ == "__main__":
    main()
