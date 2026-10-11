"""Hexagonal architecture — domain core isolated behind ports and adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    product: str
    quantity: int


class OrderRepositoryPort(ABC):
    """Outbound port — persistence contract the domain expects."""

    @abstractmethod
    def save(self, order: Order) -> str:
        ...


class NotificationPort(ABC):
    """Outbound port — external notification contract."""

    @abstractmethod
    def notify(self, message: str) -> None:
        ...


class OrderService:
    """Domain core — business rules with no infrastructure dependencies."""

    def __init__(self, repo: OrderRepositoryPort, notifier: NotificationPort) -> None:
        self._repo = repo
        self._notifier = notifier

    def place_order(self, product: str, quantity: int) -> str:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        order = Order(product=product, quantity=quantity)
        order_id = self._repo.save(order)
        self._notifier.notify(f"Order {order_id}: {quantity}x {product}")
        return order_id


class InMemoryRepository(OrderRepositoryPort):
    """Outbound adapter — in-memory persistence."""

    def __init__(self) -> None:
        self._store: dict[str, Order] = {}
        self._counter = 0

    def save(self, order: Order) -> str:
        self._counter += 1
        order_id = f"ORD-{self._counter:03d}"
        self._store[order_id] = order
        return order_id


class ConsoleNotifier(NotificationPort):
    """Outbound adapter — prints notifications to stdout."""

    def notify(self, message: str) -> None:
        print(f"[Notifier] {message}")


class CLIAdapter:
    """Inbound adapter — translates user input into domain calls."""

    def __init__(self, service: OrderService) -> None:
        self._service = service

    def handle(self, product: str, quantity: int) -> None:
        order_id = self._service.place_order(product, quantity)
        print(f"[CLI] order confirmed → {order_id}")


def main() -> None:
    repo = InMemoryRepository()
    notifier = ConsoleNotifier()
    service = OrderService(repo, notifier)
    cli = CLIAdapter(service)

    cli.handle("Widget", 3)
    cli.handle("Gadget", 1)
    print("Domain core unchanged — swap adapters for DB, HTTP, or message queues")


if __name__ == "__main__":
    main()
