"""Strangler Fig pattern — gradually replace legacy behind a routing facade."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LegacyCatalog:
    """Monolithic catalog API slated for replacement."""

    def lookup(self, sku: str) -> str:
        return f"legacy: {sku} (XML, 800 ms)"


@dataclass
class ModernCatalog:
    """New microservice-backed catalog."""

    def lookup(self, sku: str) -> str:
        return f"modern: {sku} (JSON, 40 ms)"


@dataclass
class CatalogFacade:
    """Routes traffic to modern or legacy based on a rollout map."""

    legacy: LegacyCatalog = field(default_factory=LegacyCatalog)
    modern: ModernCatalog = field(default_factory=ModernCatalog)
    modern_skus: set[str] = field(default_factory=set)

    def migrate(self, sku: str) -> None:
        self.modern_skus.add(sku)

    def lookup(self, sku: str) -> str:
        if sku in self.modern_skus:
            return self.modern.lookup(sku)
        return self.legacy.lookup(sku)


def main() -> None:
    facade = CatalogFacade()
    print(facade.lookup("WIDGET-1"))
    print(facade.lookup("GADGET-2"))

    facade.migrate("WIDGET-1")
    print(facade.lookup("WIDGET-1"))
    print(facade.lookup("GADGET-2"))

    print("Legacy shrinks SKU-by-SKU — clients keep calling the same facade")


if __name__ == "__main__":
    main()
