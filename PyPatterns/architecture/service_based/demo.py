"""Service-based architecture — few coarse-grained services instead of many microservices."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SalesService:
    """Coarse service bundling catalog, pricing, and order capture."""

    _orders: list[dict] = field(default_factory=list)

    def browse(self, category: str) -> list[str]:
        catalog = {"electronics": ["Laptop", "Phone"], "books": ["Novel", "Guide"]}
        items = catalog.get(category, [])
        print(f"[Sales] browse {category} → {items}")
        return items

    def quote(self, item: str, qty: int) -> float:
        prices = {"Laptop": 999.0, "Phone": 699.0, "Novel": 14.99, "Guide": 29.99}
        total = prices.get(item, 0.0) * qty
        print(f"[Sales] quote {qty}x {item} → ${total:.2f}")
        return total

    def checkout(self, item: str, qty: int) -> str:
        total = self.quote(item, qty)
        order_id = f"SB-{len(self._orders) + 1:03d}"
        self._orders.append({"id": order_id, "item": item, "total": total})
        print(f"[Sales] checkout complete → {order_id}")
        return order_id


@dataclass
class FulfillmentService:
    """Coarse service bundling inventory, shipping, and returns."""

    _shipments: list[str] = field(default_factory=list)

    def ship(self, order_id: str) -> None:
        tracking = f"TRK-{order_id}"
        self._shipments.append(tracking)
        print(f"[Fulfillment] shipped {order_id} tracking={tracking}")

    def status(self) -> int:
        return len(self._shipments)


def main() -> None:
    sales = SalesService()
    fulfillment = FulfillmentService()

    sales.browse("electronics")
    order_id = sales.checkout("Laptop", 1)
    fulfillment.ship(order_id)
    print(f"Two coarse services cover the domain — not dozens of microservices")


if __name__ == "__main__":
    main()
