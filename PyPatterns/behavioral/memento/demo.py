"""Memento — text editor with save/restore snapshots."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EditorMemento:
    content: str


class TextEditor:
    def __init__(self) -> None:
        self._content = ""

    def write(self, text: str) -> None:
        self._content += text

    def content(self) -> str:
        return self._content

    def save(self) -> EditorMemento:
        return EditorMemento(self._content)

    def restore(self, memento: EditorMemento) -> None:
        self._content = memento.content


class History:
    def __init__(self) -> None:
        self._snapshots: list[EditorMemento] = []

    def push(self, memento: EditorMemento) -> None:
        self._snapshots.append(memento)

    def pop(self) -> EditorMemento | None:
        if not self._snapshots:
            return None
        return self._snapshots.pop()


def main() -> None:
    editor = TextEditor()
    history = History()

    editor.write("Hello")
    history.push(editor.save())
    print(f"Saved: {editor.content()}")

    editor.write(", World!")
    print(f"Modified: {editor.content()}")

    snapshot = history.pop()
    if snapshot:
        editor.restore(snapshot)
    print(f"Restored: {editor.content()}")


if __name__ == "__main__":
    main()
