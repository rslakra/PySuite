"""Join pattern — spawn parallel tasks, wait for all to complete."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def fetch_chunk(chunk_id: int) -> tuple[int, int]:
    """Simulate I/O-bound work returning (chunk_id, byte_count)."""
    time.sleep(0.05)
    return chunk_id, (chunk_id + 1) * 100


def main() -> None:
    chunks = list(range(6))
    print(f"Fetching {len(chunks)} chunks in parallel…")

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_chunk, cid): cid for cid in chunks}
        results: list[tuple[int, int]] = []
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda item: item[0])
    total_bytes = sum(size for _, size in results)
    print("Joined results:", results)
    print(f"All {len(results)} tasks finished — {total_bytes} bytes total")


if __name__ == "__main__":
    main()
