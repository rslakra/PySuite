"""Request-Response pattern — synchronous RPC-style message exchange."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from queue import Empty, Queue
from typing import Any


@dataclass
class RpcBroker:
    """In-process broker pairing requests with correlated responses."""

    _requests: Queue[tuple[str, dict]] = field(default_factory=Queue)
    _responses: dict[str, Queue[Any]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def call(self, method: str, params: dict, timeout: float = 1.0) -> Any:
        corr_id = str(uuid.uuid4())
        reply_q: Queue[Any] = Queue(maxsize=1)
        with self._lock:
            self._responses[corr_id] = reply_q
        self._requests.put((corr_id, {"method": method, "params": params}))
        try:
            return reply_q.get(timeout=timeout)
        finally:
            with self._lock:
                self._responses.pop(corr_id, None)

    def serve_once(self) -> bool:
        try:
            corr_id, request = self._requests.get(timeout=0.05)
        except Empty:
            return False
        result = f"{request['method']}({request['params']}) → ok"
        with self._lock:
            reply_q = self._responses.get(corr_id)
        if reply_q is not None:
            reply_q.put(result)
        return True


def main() -> None:
    broker = RpcBroker()
    stop = threading.Event()

    def server_loop() -> None:
        while not stop.is_set():
            if not broker.serve_once():
                continue

    worker = threading.Thread(target=server_loop, daemon=True)
    worker.start()

    print(broker.call("get_balance", {"account": "A-1001"}))
    print(broker.call("transfer", {"from": "A-1001", "to": "B-2002", "amount": 50}))
    stop.set()
    worker.join(timeout=1.0)
    print("Client blocks until correlated response arrives — classic request/reply")


if __name__ == "__main__":
    main()
