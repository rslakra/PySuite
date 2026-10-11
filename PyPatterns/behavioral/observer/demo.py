"""Observer — stock price subject notifies display observers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def update(self, symbol: str, price: float) -> None:
        ...


class StockPriceSubject:
    def __init__(self, symbol: str, price: float) -> None:
        self.symbol = symbol
        self._price = price
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def set_price(self, price: float) -> None:
        self._price = price
        self._notify()

    def _notify(self) -> None:
        for observer in self._observers:
            observer.update(self.symbol, self._price)


class MobileAppDisplay(Observer):
    def update(self, symbol: str, price: float) -> None:
        print(f"[MobileApp] {symbol} now ${price:.2f}")


class WebDashboardDisplay(Observer):
    def update(self, symbol: str, price: float) -> None:
        print(f"[WebDashboard] {symbol} updated to ${price:.2f}")


def main() -> None:
    stock = StockPriceSubject("ACME", 100.0)
    stock.attach(MobileAppDisplay())
    stock.attach(WebDashboardDisplay())

    stock.set_price(105.50)
    stock.set_price(98.25)


if __name__ == "__main__":
    main()
