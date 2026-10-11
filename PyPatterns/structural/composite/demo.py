"""Composite pattern — file system tree of File and Directory nodes."""

from abc import ABC, abstractmethod


class FileSystemNode(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def size(self) -> int:
        ...

    @abstractmethod
    def display(self, indent: int = 0) -> str:
        ...


class File(FileSystemNode):
    def __init__(self, name: str, bytes_size: int) -> None:
        super().__init__(name)
        self.bytes_size = bytes_size

    def size(self) -> int:
        return self.bytes_size

    def display(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}{self.name} ({self.bytes_size} B)"


class Directory(FileSystemNode):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._children: list[FileSystemNode] = []

    def add(self, node: FileSystemNode) -> None:
        self._children.append(node)

    def size(self) -> int:
        return sum(child.size() for child in self._children)

    def display(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}{self.name}/ ({self.size()} B total)"]
        for child in self._children:
            lines.append(child.display(indent + 1))
        return "\n".join(lines)


def main() -> None:
    root = Directory("project")
    src = Directory("src")
    src.add(File("main.py", 1200))
    src.add(File("utils.py", 800))
    docs = Directory("docs")
    docs.add(File("README.md", 4096))
    root.add(src)
    root.add(docs)
    root.add(File("LICENSE", 1024))

    print(root.display())
    print(f"\nTotal project size: {root.size()} B")


if __name__ == "__main__":
    main()
