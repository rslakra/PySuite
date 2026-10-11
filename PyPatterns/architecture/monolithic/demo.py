"""Monolithic architecture — single deployable unit with internal modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Product:
    sku: str
    name: str
    price: float


class CatalogModule:
    """Product catalog — internal module within the monolith."""

    def __init__(self) -> None:
        self._products = {
            "W-01": Product("W-01", "Widget", 9.99),
            "G-01": Product("G-01", "Gadget", 29.99),
        }

    def get(self, sku: str) -> Product:
        product = self._products.get(sku)
        if product is None:
            raise LookupError(sku)
        return product


class OrderModule:
    """Order processing — calls catalog directly (in-process)."""

    def __init__(self, catalog: CatalogModule) -> None:
        self._catalog = catalog
        self._orders: list[dict] = []

    def place(self, sku: str, qty: int) -> str:
        product = self._catalog.get(sku)
        total = product.price * qty
        order_id = f"MONO-{len(self._orders) + 1:03d}"
        self._orders.append({"id": order_id, "sku": sku, "total": total})
        return order_id


class ReportModule:
    """Reporting — reads order state from the same process."""

    def __init__(self, orders: OrderModule) -> None:
        self._orders = orders

    def summary(self) -> str:
        count = len(self._orders._orders)
        revenue = sum(o["total"] for o in self._orders._orders)
        return f"{count} orders, ${revenue:.2f} revenue"


class MonolithApp:
    """Single entry point wiring all modules together."""

    def __init__(self) -> None:
        self.catalog = CatalogModule()
        self.orders = OrderModule(self.catalog)
        self.reports = ReportModule(self.orders)

    def run(self) -> None:
        oid1 = self.orders.place("W-01", 3)
        oid2 = self.orders.place("G-01", 1)
        print(f"[Orders] placed {oid1}, {oid2}")
        print(f"[Reports] {self.reports.summary()}")
        print("All modules share one process and one deployment artifact")


def main() -> None:
    MonolithApp().run()


if __name__ == "__main__":
    main()
