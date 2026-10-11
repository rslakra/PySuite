"""Microservices architecture — independent services communicate via message queues."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    topic: str
    payload: dict[str, Any]


class MessageQueue:
    """Simulates an async broker between services."""

    def __init__(self) -> None:
        self._queues: dict[str, deque[Message]] = {}

    def publish(self, message: Message) -> None:
        self._queues.setdefault(message.topic, deque()).append(message)

    def consume(self, topic: str) -> Message | None:
        queue = self._queues.get(topic)
        if queue:
            return queue.popleft()
        return None


@dataclass
class OrderService:
    queue: MessageQueue

    def create_order(self, order_id: str, amount: float) -> None:
        print(f"[OrderService] created {order_id} amount=${amount:.2f}")
        self.queue.publish(
            Message("billing.requests", {"order_id": order_id, "amount": amount})
        )


@dataclass
class BillingService:
    queue: MessageQueue

    def poll(self) -> None:
        msg = self.queue.consume("billing.requests")
        if msg:
            order_id = msg.payload["order_id"]
            amount = msg.payload["amount"]
            print(f"[BillingService] charged {order_id} ${amount:.2f}")
            self.queue.publish(
                Message("shipping.requests", {"order_id": order_id})
            )


@dataclass
class ShippingService:
    queue: MessageQueue

    def poll(self) -> None:
        msg = self.queue.consume("shipping.requests")
        if msg:
            order_id = msg.payload["order_id"]
            print(f"[ShippingService] dispatched {order_id}")


def main() -> None:
    bus = MessageQueue()
    orders = OrderService(bus)
    billing = BillingService(bus)
    shipping = ShippingService(bus)

    orders.create_order("MS-001", 59.99)
    billing.poll()
    shipping.poll()
    print("Each service owns its data and communicates only through messages")


if __name__ == "__main__":
    main()
