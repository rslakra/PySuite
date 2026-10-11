"""Async messaging — fire-and-forget publish on a message bus."""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    topic: str
    body: str


class MessageBus:
    """In-memory pub/sub; publishers never wait for subscriber completion."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[threading.Thread]] = defaultdict(list)
        self._delivered: list[str] = []

    def subscribe(self, topic: str, name: str) -> None:
        def handler() -> None:
            time.sleep(0.02)
            self._delivered.append(f"[{name}] handled {topic}")

        thread = threading.Thread(target=handler, name=name, daemon=True)
        self._subscribers[topic].append(thread)

    def publish(self, message: Message) -> None:
        print(f"Publisher fired → {message.topic}: {message.body} (no wait)")
        for thread in self._subscribers[message.topic]:
            thread.start()

    def join_handlers(self) -> list[str]:
        for threads in self._subscribers.values():
            for thread in threads:
                thread.join(timeout=0.5)
        return self._delivered


def main() -> None:
    bus = MessageBus()
    bus.subscribe("order.placed", "billing")
    bus.subscribe("order.placed", "inventory")

    bus.publish(Message("order.placed", "ORD-9001"))
    print("Publisher returned immediately — handlers run concurrently")
    for line in bus.join_handlers():
        print(line)


if __name__ == "__main__":
    main()
