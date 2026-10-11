"""Messaging pattern — threads exchange messages via a shared Queue."""

from __future__ import annotations

import threading
import time
from queue import Empty, Queue


def producer(outbox: Queue[str], worker_id: int) -> None:
    for step in range(3):
        message = f"worker-{worker_id}: step-{step}"
        outbox.put(message)
        time.sleep(0.02)


def consumer(inbox: Queue[str], name: str, stop_event: threading.Event) -> None:
    while not stop_event.is_set() or not inbox.empty():
        try:
            message = inbox.get(timeout=0.05)
        except Empty:
            continue
        print(f"[{name}] received → {message}")
        inbox.task_done()


def main() -> None:
    mailbox: Queue[str] = Queue()
    stop = threading.Event()

    receiver = threading.Thread(target=consumer, args=(mailbox, "dispatcher", stop))
    receiver.start()

    senders = [
        threading.Thread(target=producer, args=(mailbox, worker_id))
        for worker_id in range(3)
    ]
    for sender in senders:
        sender.start()
    for sender in senders:
        sender.join()

    mailbox.join()
    stop.set()
    receiver.join(timeout=1.0)
    print("All messages delivered via queue — no shared mutable state between threads")


if __name__ == "__main__":
    main()
