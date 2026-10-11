"""Visitor — shopping cart accepts tax and discount visitors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CartItem:
    name: str
    price: float


class Cart:
    def __init__(self, items: list[CartItem] | None = None) -> None:
        self.items = list(items or [])

    def accept(self, visitor: CartVisitor) -> float:
        return visitor.visit(self)


class CartVisitor(ABC):
    @abstractmethod
    def visit(self, cart: Cart) -> float:
        ...


class TaxVisitor(CartVisitor):
    def __init__(self, rate: float) -> None:
        self._rate = rate

    def visit(self, cart: Cart) -> float:
        subtotal = sum(item.price for item in cart.items)
        tax = subtotal * self._rate
        print(f"Tax ({self._rate:.0%}): ${tax:.2f}")
        return subtotal + tax


class DiscountVisitor(CartVisitor):
    def __init__(self, discount: float) -> None:
        self._discount = discount

    def visit(self, cart: Cart) -> float:
        subtotal = sum(item.price for item in cart.items)
        total = max(subtotal - self._discount, 0.0)
        print(f"Discount applied: -${self._discount:.2f}")
        return total


def main() -> None:
    cart = Cart(
        [
            CartItem("Keyboard", 79.99),
            CartItem("Mouse", 29.99),
        ]
    )

    print(f"With tax: ${cart.accept(TaxVisitor(0.08)):.2f}")
    print(f"With discount: ${cart.accept(DiscountVisitor(10.0)):.2f}")


if __name__ == "__main__":
    main()
