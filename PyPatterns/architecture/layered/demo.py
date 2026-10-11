"""Layered architecture — presentation, business, and data tiers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProductRecord:
    sku: str
    name: str
    price: float


class DataLayer:
    """Persistence tier — simulates a database."""

    def __init__(self) -> None:
        self._catalog: dict[str, ProductRecord] = {
            "SKU-001": ProductRecord("SKU-001", "Widget", 19.99),
            "SKU-002": ProductRecord("SKU-002", "Gadget", 49.99),
        }

    def find_by_sku(self, sku: str) -> ProductRecord | None:
        return self._catalog.get(sku)

    def save_order(self, sku: str, quantity: int, total: float) -> str:
        order_id = f"ORD-{sku}-{quantity}"
        print(f"[Data] persisted order {order_id} total=${total:.2f}")
        return order_id


class BusinessLayer:
    """Domain logic tier — pricing rules and validation."""

    def __init__(self, data: DataLayer) -> None:
        self._data = data

    def calculate_order(self, sku: str, quantity: int) -> tuple[str, float]:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        product = self._data.find_by_sku(sku)
        if product is None:
            raise LookupError(f"unknown SKU: {sku}")
        discount = 0.10 if quantity >= 5 else 0.0
        total = product.price * quantity * (1 - discount)
        order_id = self._data.save_order(sku, quantity, total)
        return order_id, total


class PresentationLayer:
    """UI tier — formats output for the user."""

    def __init__(self, business: BusinessLayer) -> None:
        self._business = business

    def place_order(self, sku: str, quantity: int) -> None:
        order_id, total = self._business.calculate_order(sku, quantity)
        print(f"[UI] order {order_id} placed — total ${total:.2f}")


def main() -> None:
    data = DataLayer()
    business = BusinessLayer(data)
    ui = PresentationLayer(business)

    ui.place_order("SKU-001", 2)
    ui.place_order("SKU-002", 5)
    print("Each layer depends only on the layer directly below it")


if __name__ == "__main__":
    main()
