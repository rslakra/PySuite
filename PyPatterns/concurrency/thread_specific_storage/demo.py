"""Thread-specific storage — per-thread context via threading.local()."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass
class RequestContext:
    request_id: int
    user: str


class RequestScope:
    """Provides isolated context for each thread (like a per-request scope)."""

    def __init__(self) -> None:
        self._local = threading.local()

    def bind(self, context: RequestContext) -> None:
        self._local.context = context

    def current(self) -> RequestContext:
        ctx = getattr(self._local, "context", None)
        if ctx is None:
            raise RuntimeError("No request context bound on this thread")
        return ctx

    def clear(self) -> None:
        if hasattr(self._local, "context"):
            del self._local.context


def handle_request(scope: RequestScope, request_id: int, user: str) -> str:
    scope.bind(RequestContext(request_id=request_id, user=user))
    time.sleep(0.02)
    ctx = scope.current()
    scope.clear()
    return f"[{threading.current_thread().name}] request={ctx.request_id} user={ctx.user}"


def main() -> None:
    scope = RequestScope()
    threads: list[threading.Thread] = []
    results: list[str] = []

    def worker(rid: int, user: str) -> None:
        results.append(handle_request(scope, rid, user))

    print("Running concurrent requests with thread-local context...")
    for i in range(5):
        t = threading.Thread(target=worker, args=(i, f"user-{i}"), name=f"req-{i}")
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    for line in sorted(results):
        print(line)
    print("Each thread saw only its own RequestContext — no cross-thread leakage")


if __name__ == "__main__":
    main()
