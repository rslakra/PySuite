"""Publish-Subscribe pattern — topic-based event distribution."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable


Subscriber = Callable[[str, dict], None]


@dataclass
class EventBus:
    """Topic router: publishers emit events; subscribers receive by topic."""

    _subscribers: dict[str, list[Subscriber]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def subscribe(self, topic: str, handler: Subscriber) -> None:
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, event: dict) -> int:
        delivered = 0
        for handler in self._subscribers[topic]:
            handler(topic, event)
            delivered += 1
        return delivered


def main() -> None:
    bus = EventBus()

    bus.subscribe("orders", lambda t, e: print(f"  billing ← {t}: {e['id']}"))
    bus.subscribe("orders", lambda t, e: print(f"  shipping ← {t}: {e['id']}"))
    bus.subscribe("inventory", lambda t, e: print(f"  warehouse ← {t}: sku={e['sku']}"))

    print("Publishing orders.created:")
    count = bus.publish("orders", {"id": "ORD-42", "total": 199.0})
    print(f"  → {count} subscribers notified")

    print("Publishing inventory.low:")
    bus.publish("inventory", {"sku": "WIDGET-9", "qty": 3})
    print("Publishers know topics, not individual subscribers")


if __name__ == "__main__":
    main()
