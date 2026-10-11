"""Exclusive ownership — pass object ownership via Queue; no shared mutable state."""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass

_SENTINEL = object()


@dataclass
class WorkItem:
    item_id: int
    value: int = 0


def _stage(
    name: str,
    inbox: queue.Queue,
    outbox: queue.Queue,
    transform,
) -> None:
    while True:
        item = inbox.get()
        if item is _SENTINEL:
            outbox.put(_SENTINEL)
            break
        print(f"[{name}] owns item {item.item_id} (value={item.value})")
        transform(item)
        time.sleep(0.01)
        outbox.put(item)


def main() -> None:
    items = [WorkItem(i, value=i) for i in range(5)]
    stage1_in: queue.Queue = queue.Queue()
    stage2_in: queue.Queue = queue.Queue()
    results_q: queue.Queue = queue.Queue()

    t1 = threading.Thread(
        target=_stage,
        args=("stage-a", stage1_in, stage2_in, lambda w: setattr(w, "value", w.value + 10)),
        daemon=True,
    )
    t2 = threading.Thread(
        target=_stage,
        args=("stage-b", stage2_in, results_q, lambda w: setattr(w, "value", w.value * 2)),
        daemon=True,
    )

    print("Processing items with exclusive ownership hand-offs...")
    t1.start()
    t2.start()

    for item in items:
        stage1_in.put(item)
    stage1_in.put(_SENTINEL)

    t1.join()
    t2.join()

    results: list[WorkItem] = []
    while True:
        item = results_q.get()
        if item is _SENTINEL:
            break
        results.append(item)

    for item in sorted(results, key=lambda w: w.item_id):
        print(f"item {item.item_id} final value={item.value}")
    print("No thread shared mutable WorkItem state — ownership moved via queues")


if __name__ == "__main__":
    main()
