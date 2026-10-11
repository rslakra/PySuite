"""Backends for Frontends — tailor one core service to each client channel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    sku: str
    title: str
    price_cents: int
    description: str
    image_urls: tuple[str, ...]


class CatalogService:
    """Shared domain service — not exposed directly to clients."""

    def get_product(self, sku: str) -> Product:
        return Product(
            sku=sku,
            title="Trail Runner X",
            price_cents=8999,
            description="Lightweight trail shoe with Gore-Tex upper and Vibram sole.",
            image_urls=("hero.jpg", "side.jpg", "sole.jpg", "lifestyle.jpg"),
        )


class WebBFF:
    """Rich product page for desktop browsers."""

    def __init__(self, catalog: CatalogService) -> None:
        self._catalog = catalog

    def product_page(self, sku: str) -> dict[str, object]:
        product = self._catalog.get_product(sku)
        return {
            "layout": "desktop-grid",
            "title": product.title,
            "price": f"${product.price_cents / 100:.2f}",
            "gallery": list(product.image_urls),
            "long_description": product.description,
        }


class MobileBFF:
    """Compact payload for mobile apps on slow networks."""

    def __init__(self, catalog: CatalogService) -> None:
        self._catalog = catalog

    def product_card(self, sku: str) -> dict[str, object]:
        product = self._catalog.get_product(sku)
        return {
            "layout": "mobile-card",
            "title": product.title,
            "price_cents": product.price_cents,
            "thumb": product.image_urls[0],
            "summary": product.description[:48] + "...",
        }


def main() -> None:
    catalog = CatalogService()
    web = WebBFF(catalog)
    mobile = MobileBFF(catalog)

    print("Same SKU, different BFF shapes:")
    print(f"  Web:    {web.product_page('SKU-42')}")
    print(f"  Mobile: {mobile.product_card('SKU-42')}")
    print("Each frontend gets an API tailored to its UX — core service stays unchanged")


if __name__ == "__main__":
    main()
