"""Event-driven architecture — publishers emit events on a shared event bus."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable


EventHandler = Callable[[dict], None]


class EventBus:
    """Central broker routing events to registered subscribers."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event_type: str, payload: dict) -> None:
        for handler in self._subscribers[event_type]:
            handler(payload)


@dataclass(frozen=True)
class OrderPlaced:
    order_id: str
    amount: float


def inventory_handler(payload: dict) -> None:
    print(f"[Inventory] reserve stock for order {payload['order_id']}")


def billing_handler(payload: dict) -> None:
    print(f"[Billing] charge ${payload['amount']:.2f} for order {payload['order_id']}")


def shipping_handler(payload: dict) -> None:
    print(f"[Shipping] schedule delivery for order {payload['order_id']}")


def main() -> None:
    bus = EventBus()
    bus.subscribe("order.placed", inventory_handler)
    bus.subscribe("order.placed", billing_handler)
    bus.subscribe("order.placed", shipping_handler)

    order = OrderPlaced(order_id="ORD-42", amount=129.99)
    print(f"Publisher: order placed → {order.order_id}")
    bus.publish("order.placed", {"order_id": order.order_id, "amount": order.amount})
    print("Subscribers notified asynchronously via event bus")


if __name__ == "__main__":
    main()
