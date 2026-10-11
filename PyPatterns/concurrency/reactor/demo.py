"""Reactor pattern — demux events from a queue, dispatch to handlers."""

from __future__ import annotations

import queue
import select
import socket
import threading
import time
from collections.abc import Callable


EventHandler = Callable[[str], None]


class Reactor:
    """Single-threaded event loop: queue + select wakeup, handler dispatch."""

    def __init__(self) -> None:
        self._handlers: dict[str, EventHandler] = {}
        self._events: queue.Queue[tuple[str, str]] = queue.Queue()
        self._read, self._write = socket.socketpair()
        self._read.setblocking(False)

    def register(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type] = handler

    def post(self, event_type: str, payload: str) -> None:
        self._events.put((event_type, payload))
        self._write.send(b"\x01")  # wake select()

    def run(self, timeout: float = 2.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            remaining = max(0.0, deadline - time.monotonic())
            readable, _, _ = select.select([self._read], [], [], min(0.1, remaining))
            if readable:
                self._read.recv(1024)
            while True:
                try:
                    event_type, payload = self._events.get_nowait()
                except queue.Empty:
                    break
                handler = self._handlers.get(event_type)
                if handler:
                    handler(payload)


def main() -> None:
    reactor = Reactor()
    reactor.register("order", lambda msg: print(f"[OrderHandler]   {msg}"))
    reactor.register("inventory", lambda msg: print(f"[InventoryHandler] {msg}"))

    def producer() -> None:
        reactor.post("order", "order-101 placed")
        time.sleep(0.05)
        reactor.post("inventory", "sku-42 reserved")
        time.sleep(0.05)
        reactor.post("order", "order-101 confirmed")

    threading.Thread(target=producer, daemon=True).start()
    reactor.run(timeout=1.0)
    print("Reactor demuxed events from queue and dispatched to typed handlers")


if __name__ == "__main__":
    main()
