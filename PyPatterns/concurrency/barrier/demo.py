"""Barrier — threads wait until all participants reach the barrier before proceeding."""

from __future__ import annotations

import threading
import time


def worker(barrier: threading.Barrier, name: str, delay: float) -> None:
    print(f"[{name}] working...")
    time.sleep(delay)
    print(f"[{name}] reached barrier (waiting for others)")
    idx = barrier.wait()
    if idx == 0:
        print(f"[{name}] releases barrier — all {barrier.parties} threads synchronized")
    print(f"[{name}] continues after barrier")


def main() -> None:
    barrier = threading.Barrier(3)
    threads = [
        threading.Thread(target=worker, args=(barrier, "A", 0.1)),
        threading.Thread(target=worker, args=(barrier, "B", 0.3)),
        threading.Thread(target=worker, args=(barrier, "C", 0.2)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("All workers passed the barrier.")


if __name__ == "__main__":
    main()
