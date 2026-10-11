"""Flyweight pattern — shared TreeType intrinsic state for many Tree instances."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TreeType:
    """Intrinsic (shared) state: name, color, texture."""

    name: str
    color: str
    texture: str

    def render(self, x: int, y: int) -> str:
        return f"{self.name} ({self.color}, {self.texture}) at ({x}, {y})"


class TreeTypeFactory:
    _pool: dict[tuple[str, str, str], TreeType] = {}

    @classmethod
    def get(cls, name: str, color: str, texture: str) -> TreeType:
        key = (name, color, texture)
        if key not in cls._pool:
            cls._pool[key] = TreeType(name, color, texture)
            print(f"  [factory] Created shared type: {name}")
        return cls._pool[key]

    @classmethod
    def pool_size(cls) -> int:
        return len(cls._pool)


class Tree:
    """Extrinsic state: position. Intrinsic state comes from TreeType."""

    def __init__(self, x: int, y: int, tree_type: TreeType) -> None:
        self.x = x
        self.y = y
        self.type = tree_type

    def draw(self) -> str:
        return self.type.render(self.x, self.y)


def main() -> None:
    factory = TreeTypeFactory
    oak = factory.get("Oak", "green", "rough")
    pine = factory.get("Pine", "dark-green", "smooth")
    factory.get("Oak", "green", "rough")  # reuses existing Oak type

    forest = [
        Tree(10, 20, oak),
        Tree(30, 40, pine),
        Tree(50, 60, oak),
        Tree(70, 80, pine),
    ]
    print("Rendering forest:")
    for tree in forest:
        print(f"  {tree.draw()}")
    print(f"\nTrees placed: {len(forest)}, shared types: {factory.pool_size()}")


if __name__ == "__main__":
    main()
