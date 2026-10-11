"""Active Object — client calls proxy; scheduler thread executes on servant."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Callable


@dataclass
class MethodRequest:
    """Queued invocation with optional completion callback."""

    operation: Callable[[], object]
    result: queue.Queue[object]


class CounterServant:
    """Real object whose methods run only on the scheduler thread."""

    def __init__(self) -> None:
        self.value = 0

    def increment(self, amount: int) -> int:
        self.value += amount
        return self.value

    def read(self) -> int:
        return self.value


class CounterProxy:
    """Proxy: enqueue requests; scheduler executes them on the servant."""

    def __init__(self, servant: CounterServant) -> None:
        self._servant = servant
        self._requests: queue.Queue[MethodRequest | None] = queue.Queue()
        self._scheduler = threading.Thread(target=self._run, daemon=True)
        self._scheduler.start()

    def _run(self) -> None:
        while True:
            request = self._requests.get()
            if request is None:
                break
            try:
                request.result.put(request.operation())
            except Exception as exc:  # noqa: BLE001 — demo surfaces worker errors
                request.result.put(exc)

    def _dispatch(self, operation: Callable[[], object]) -> object:
        result: queue.Queue[object] = queue.Queue(maxsize=1)
        self._requests.put(MethodRequest(operation, result))
        outcome = result.get(timeout=2.0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def increment(self, amount: int) -> int:
        return self._dispatch(lambda: self._servant.increment(amount))

    def read(self) -> int:
        return self._dispatch(self._servant.read)

    def shutdown(self) -> None:
        self._requests.put(None)
        self._scheduler.join(timeout=2.0)


def main() -> None:
    proxy = CounterProxy(CounterServant())

    def worker(n: int) -> None:
        proxy.increment(n)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(1, 6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print(f"Final counter value (via proxy): {proxy.read()}")
    proxy.shutdown()


if __name__ == "__main__":
    main()
