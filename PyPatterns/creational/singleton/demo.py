"""Singleton — thread-safe double-checked locking for a single shared instance."""

import threading


class Singleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "counter"):
            self.counter = 0


def main() -> None:
    a = Singleton()
    b = Singleton()
    print(f"Same instance: {a is b}")
    print(f"id(a)={id(a)}, counter={a.counter}")

    a.counter = 1
    print(f"Shared state via b: counter={b.counter}")

    seen_ids: list[int] = []

    def worker() -> None:
        s = Singleton()
        s.counter += 1
        seen_ids.append(id(s))

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"All threads saw same id: {len(set(seen_ids)) == 1}")
    print(f"After 5 threads: counter={Singleton().counter}")


if __name__ == "__main__":
    main()
