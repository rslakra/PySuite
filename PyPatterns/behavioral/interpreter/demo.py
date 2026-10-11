"""Interpreter — simple arithmetic expression evaluator."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Expression(ABC):
    @abstractmethod
    def interpret(self) -> int:
        ...


class Number(Expression):
    def __init__(self, value: int) -> None:
        self._value = value

    def interpret(self) -> int:
        return self._value


class Add(Expression):
    def __init__(self, left: Expression, right: Expression) -> None:
        self._left = left
        self._right = right

    def interpret(self) -> int:
        return self._left.interpret() + self._right.interpret()


class Subtract(Expression):
    def __init__(self, left: Expression, right: Expression) -> None:
        self._left = left
        self._right = right

    def interpret(self) -> int:
        return self._left.interpret() - self._right.interpret()


def main() -> None:
    # Build expression tree for: 5 + 3
    expression = Add(Number(5), Number(3))
    result = expression.interpret()
    print(f"5 + 3 = {result}")


if __name__ == "__main__":
    main()
