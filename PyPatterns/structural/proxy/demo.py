"""Proxy pattern — ImageProxy lazy-loads an expensive RealImage."""

from abc import ABC, abstractmethod
import time


class Image(ABC):
    @abstractmethod
    def display(self) -> str:
        ...


class RealImage(Image):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        print(f"  [RealImage] Loading '{self.filename}' from disk...")
        time.sleep(0.1)  # simulate expensive I/O

    def display(self) -> str:
        return f"Displaying high-res '{self.filename}'"


class ImageProxy(Image):
    """Defers RealImage creation until first display."""

    def __init__(self, filename: str) -> None:
        self._filename = filename
        self._real: RealImage | None = None

    def display(self) -> str:
        if self._real is None:
            print(f"  [Proxy] First access — creating RealImage for '{self._filename}'")
            self._real = RealImage(self._filename)
        return self._real.display()


def main() -> None:
    print("Creating proxy (no disk load yet)...")
    photo = ImageProxy("vacation.jpg")

    print("\nFirst display:")
    print(photo.display())

    print("\nSecond display (cached):")
    print(photo.display())


if __name__ == "__main__":
    main()
