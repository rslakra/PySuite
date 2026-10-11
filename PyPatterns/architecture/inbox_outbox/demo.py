"""Transactional outbox — persist events in the same transaction as domain data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class OutboxEvent:
    event_id: int
    aggregate: str
    payload: str
    published: bool = False


@dataclass
class Transaction:
    """Simulates a DB transaction: commit writes orders and outbox together."""

    orders: list[str] = field(default_factory=list)
    outbox: list[OutboxEvent] = field(default_factory=list)
    _next_id: int = 1

    def place_order(self, order_id: str) -> OutboxEvent:
        event = OutboxEvent(
            event_id=self._next_id,
            aggregate=order_id,
            payload=f"OrderPlaced:{order_id}",
        )
        self._next_id += 1
        self.orders.append(order_id)
        self.outbox.append(event)
        return event


class OutboxPublisher:
    """Background worker that publishes pending outbox rows after commit."""

    def publish_pending(self, tx: Transaction) -> list[str]:
        published: list[str] = []
        for event in tx.outbox:
            if event.published:
                continue
            stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
            published.append(f"[{stamp}] bus ← {event.payload}")
            event.published = True
        return published


def main() -> None:
    tx = Transaction()
    publisher = OutboxPublisher()

    print("Placing orders inside a single transactional unit...")
    for order_id in ("ORD-101", "ORD-102"):
        event = tx.place_order(order_id)
        print(f"  committed order {order_id} + outbox row {event.event_id}")

    print(f"\nOutbox pending: {sum(1 for e in tx.outbox if not e.published)}")
    for line in publisher.publish_pending(tx):
        print(line)
    print(f"Outbox pending after publish: {sum(1 for e in tx.outbox if not e.published)}")
    print("Domain write and event publish are decoupled but never lost")


if __name__ == "__main__":
    main()
