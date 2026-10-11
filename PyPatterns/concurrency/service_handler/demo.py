"""Service handler — thread-per-request task server."""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    request_id: int
    payload: str


class ServiceHandler:
    """Accepts requests and spawns one handler thread per request."""

    def __init__(self) -> None:
        self._requests: queue.Queue[Request] = queue.Queue()
        self._handlers: list[threading.Thread] = []
        self._lock = threading.Lock()

    def submit(self, request: Request) -> None:
        self._requests.put(request)

    def _handle(self, request: Request) -> None:
        name = threading.current_thread().name
        print(f"[{name}] start request {request.request_id}: {request.payload}")
        time.sleep(0.02)
        print(f"[{name}] done  request {request.request_id}")

    def dispatch(self, request: Request) -> threading.Thread:
        """Spawn a dedicated handler thread for one request."""
        thread = threading.Thread(
            target=self._handle,
            args=(request,),
            name=f"handler-{request.request_id}",
            daemon=True,
        )
        with self._lock:
            self._handlers.append(thread)
        thread.start()
        return thread

    def drain(self) -> None:
        """Process every queued request with a new thread."""
        while True:
            try:
                request = self._requests.get_nowait()
            except queue.Empty:
                break
            self.dispatch(request)

    def join_all(self) -> None:
        for thread in self._handlers:
            thread.join()


def main() -> None:
    server = ServiceHandler()
    for i in range(5):
        server.submit(Request(i, f"payload-{i}"))

    print("Dispatching thread-per-request handlers...")
    server.drain()
    server.join_all()
    print(f"Completed {len(server._handlers)} requests on separate threads")


if __name__ == "__main__":
    main()
