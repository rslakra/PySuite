"""Bridge pattern — Shape abstraction decoupled from Renderer implementation."""

from abc import ABC, abstractmethod


class Renderer(ABC):
    @abstractmethod
    def render_circle(self, radius: float) -> str:
        ...


class VectorRenderer(Renderer):
    def render_circle(self, radius: float) -> str:
        return f"Drawing circle (r={radius}) as vector paths"


class RasterRenderer(Renderer):
    def render_circle(self, radius: float) -> str:
        return f"Drawing circle (r={radius}) as pixel bitmap"


class Shape(ABC):
    def __init__(self, renderer: Renderer) -> None:
        self._renderer = renderer

    @abstractmethod
    def draw(self) -> str:
        ...


class Circle(Shape):
    def __init__(self, renderer: Renderer, radius: float) -> None:
        super().__init__(renderer)
        self.radius = radius

    def draw(self) -> str:
        return self._renderer.render_circle(self.radius)


def main() -> None:
    vector = VectorRenderer()
    raster = RasterRenderer()

    shapes = [
        Circle(vector, 5.0),
        Circle(raster, 5.0),
        Circle(vector, 12.5),
    ]
    for shape in shapes:
        print(shape.draw())


if __name__ == "__main__":
    main()
