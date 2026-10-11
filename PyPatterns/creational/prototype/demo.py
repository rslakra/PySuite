"""Prototype — clone existing objects instead of constructing from scratch."""

import copy
from dataclasses import dataclass


@dataclass
class Shape:
    kind: str
    color: str
    points: list[tuple[int, int]]

    def clone(self) -> "Shape":
        return copy.deepcopy(self)

    def describe(self) -> str:
        return f"{self.kind} ({self.color}) @ {self.points}"


def main() -> None:
    circle = Shape("Circle", "red", [(0, 0), (10, 0)])
    print("Original:", circle.describe())

    clone = circle.clone()
    clone.color = "blue"
    clone.points.append((5, 5))

    print("Clone (modified):", clone.describe())
    print("Original (unchanged):", circle.describe())
    print("Distinct objects:", circle is not clone)


if __name__ == "__main__":
    main()
