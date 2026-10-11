"""Decorator pattern — coffee beverages with add-on decorators."""

from abc import ABC, abstractmethod


class Coffee(ABC):
    @abstractmethod
    def cost(self) -> float:
        ...

    @abstractmethod
    def description(self) -> str:
        ...


class SimpleCoffee(Coffee):
    def cost(self) -> float:
        return 2.00

    def description(self) -> str:
        return "Simple coffee"


class CoffeeDecorator(Coffee, ABC):
    def __init__(self, coffee: Coffee) -> None:
        self._coffee = coffee


class Milk(CoffeeDecorator):
    def cost(self) -> float:
        return self._coffee.cost() + 0.50

    def description(self) -> str:
        return f"{self._coffee.description()}, milk"


class Sugar(CoffeeDecorator):
    def cost(self) -> float:
        return self._coffee.cost() + 0.25

    def description(self) -> str:
        return f"{self._coffee.description()}, sugar"


def main() -> None:
    drinks: list[Coffee] = [
        SimpleCoffee(),
        Milk(SimpleCoffee()),
        Sugar(Milk(SimpleCoffee())),
    ]
    for drink in drinks:
        print(f"{drink.description():30} ${drink.cost():.2f}")


if __name__ == "__main__":
    main()
