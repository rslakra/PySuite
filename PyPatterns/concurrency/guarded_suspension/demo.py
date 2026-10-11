"""Guarded suspension — consumer waits on Condition until buffer has items."""

from __future__ import annotations

import threading
import time
from collections import deque


class BoundedBuffer[T]:
    """Producer fills buffer; consumer suspends until items are available."""

    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._items: deque[T] = deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

    def put(self, item: T) -> None:
        with self._not_full:
            while len(self._items) >= self._capacity:
                self._not_full.wait(timeout=1.0)
            self._items.append(item)
            self._not_empty.notify()

    def get(self) -> T:
        with self._not_empty:
            while not self._items:
                self._not_empty.wait(timeout=1.0)
            item = self._items.popleft()
            self._not_full.notify()
            return item


def main() -> None:
    buffer: BoundedBuffer[str] = BoundedBuffer(capacity=2)
    consumed: list[str] = []

    def producer() -> None:
        for index in range(4):
            label = f"item-{index}"
            buffer.put(label)
            print(f"Produced {label}")
            time.sleep(0.02)

    def consumer() -> None:
        for _ in range(4):
            item = buffer.get()
            consumed.append(item)
            print(f"Consumed {item}")

    prod = threading.Thread(target=producer)
    cons = threading.Thread(target=consumer)
    cons.start()
    time.sleep(0.03)
    prod.start()
    prod.join()
    cons.join()

    print(f"Consumed in order: {consumed}")


if __name__ == "__main__":
    main()
