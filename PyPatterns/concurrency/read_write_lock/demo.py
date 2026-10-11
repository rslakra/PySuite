"""Read-write lock — many concurrent readers, one exclusive writer."""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from collections.abc import Iterator


class ReadWriteLock:
    """Simple RW lock: first reader blocks writers; writer blocks everyone."""

    def __init__(self) -> None:
        self._mutex = threading.Lock()
        self._write_lock = threading.Lock()
        self._readers = 0

    @contextmanager
    def read(self) -> Iterator[None]:
        with self._mutex:
            self._readers += 1
            if self._readers == 1:
                self._write_lock.acquire()
        try:
            yield
        finally:
            with self._mutex:
                self._readers -= 1
                if self._readers == 0:
                    self._write_lock.release()

    @contextmanager
    def write(self) -> Iterator[None]:
        with self._write_lock:
            yield


class SharedCache:
    def __init__(self) -> None:
        self._data: dict[str, int] = {"hits": 0}
        self._rw = ReadWriteLock()

    def read_hits(self) -> int:
        with self._rw.read():
            time.sleep(0.02)
            return self._data["hits"]

    def increment_hits(self) -> None:
        with self._rw.write():
            time.sleep(0.03)
            self._data["hits"] += 1


def main() -> None:
    cache = SharedCache()
    cache.increment_hits()

    readers = [
        threading.Thread(target=lambda i=i: print(f"Reader-{i}: hits={cache.read_hits()}"))
        for i in range(4)
    ]
    writer = threading.Thread(
        target=lambda: (cache.increment_hits(), print("Writer: incremented hits"))
    )

    start = time.perf_counter()
    for reader in readers:
        reader.start()
    for reader in readers:
        reader.join()
    writer.start()
    writer.join()
    elapsed = time.perf_counter() - start

    print(f"Final hits: {cache.read_hits()} (elapsed {elapsed:.2f}s — readers ran concurrently)")
    print("Writer ran exclusively after readers finished")


if __name__ == "__main__":
    main()
