from abc import ABC, abstractmethod
from pathlib import Path


class AbstractConverter(ABC):
    """Base class for document format converters."""

    source_extensions: frozenset[str]
    dest_extensions: frozenset[str]

    @abstractmethod
    def convert(self, source: Path, destination: Path) -> None:
        """Convert source file to destination file."""
