"""Strategy — interchangeable payment strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Order:
    amount: float


class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, order: Order) -> str:
        ...


class CreditCardPayment(PaymentStrategy):
    def __init__(self, card_number: str) -> None:
        self._card_number = card_number

    def pay(self, order: Order) -> str:
        last_four = self._card_number[-4:]
        return f"Paid ${order.amount:.2f} with credit card ending {last_four}"


class PayPalPayment(PaymentStrategy):
    def __init__(self, email: str) -> None:
        self._email = email

    def pay(self, order: Order) -> str:
        return f"Paid ${order.amount:.2f} via PayPal ({self._email})"


class Checkout:
    def __init__(self, strategy: PaymentStrategy) -> None:
        self._strategy = strategy

    def set_strategy(self, strategy: PaymentStrategy) -> None:
        self._strategy = strategy

    def complete(self, order: Order) -> str:
        return self._strategy.pay(order)


def main() -> None:
    order = Order(amount=49.99)

    checkout = Checkout(CreditCardPayment("4111111111111111"))
    print(checkout.complete(order))

    checkout.set_strategy(PayPalPayment("user@example.com"))
    print(checkout.complete(order))


if __name__ == "__main__":
    main()
