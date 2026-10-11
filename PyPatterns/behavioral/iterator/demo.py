"""Iterator — custom BookCollection iterator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class Book:
    title: str
    author: str


class BookCollection:
    def __init__(self, books: list[Book] | None = None) -> None:
        self._books: list[Book] = list(books or [])

    def add(self, book: Book) -> None:
        self._books.append(book)

    def __iter__(self) -> Iterator[Book]:
        return BookIterator(self._books)


class BookIterator:
    def __init__(self, books: list[Book]) -> None:
        self._books = books
        self._index = 0

    def __iter__(self) -> BookIterator:
        return self

    def __next__(self) -> Book:
        if self._index >= len(self._books):
            raise StopIteration
        book = self._books[self._index]
        self._index += 1
        return book


def main() -> None:
    collection = BookCollection(
        [
            Book("Clean Code", "Robert C. Martin"),
            Book("Design Patterns", "GoF"),
            Book("The Pragmatic Programmer", "Hunt & Thomas"),
        ]
    )
    for book in collection:
        print(f"{book.title} by {book.author}")


if __name__ == "__main__":
    main()
