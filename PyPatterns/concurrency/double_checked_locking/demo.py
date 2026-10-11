"""Double-checked locking — thread-safe lazy initialization of a shared resource."""

from __future__ import annotations

import threading


class LazyConfig:
    """Expensive config object created once under contention."""

    _instance: LazyConfig | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.settings = {"timeout_ms": 500, "retries": 3}

    @classmethod
    def instance(cls) -> LazyConfig:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance


def main() -> None:
    seen: list[int] = []

    def worker() -> None:
        config = LazyConfig.instance()
        seen.append(id(config))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    singleton = LazyConfig.instance()
    print(f"Single instance: {len(set(seen)) == 1}")
    print(f"Settings: {singleton.settings}")


if __name__ == "__main__":
    main()
