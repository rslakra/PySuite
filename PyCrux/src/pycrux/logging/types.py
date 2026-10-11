"""Logging enumerations."""

from __future__ import annotations

from enum import IntEnum
from typing import Self

from pycrux.enums import BaseEnum, CaseInsensitiveEnum

# Alternative spellings accepted by ``LogFormat.from_string``.
_FORMAT_ALIASES = {
    "txt": "text",
    "log": "text",
    "jsonl": "json",
    "ndjson": "json",
}


class LogLevel(BaseEnum, IntEnum):
    """Log severity; members compare equal to the matching stdlib ``logging`` level numbers."""

    CRITICAL = 50
    ERROR = 40
    WARN = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    @classmethod
    def from_string(cls, value: Self | str | None) -> Self:
        """Parse a level name (case-insensitive), e.g. ``"warn"`` or ``"ERROR"``."""
        if isinstance(value, cls):
            return value
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Invalid {cls.__name__}: expected non-empty string, got {value!r}")
        try:
            return cls[value.strip().upper()]
        except KeyError:
            valid = ", ".join(cls.names())
            raise ValueError(f"Invalid {cls.__name__}: {value!r}. Valid values are: {valid}") from None


class LogFormat(CaseInsensitiveEnum):
    """Output format of a log destination."""

    TEXT = "text"
    JSON = "json"
    XML = "xml"

    @classmethod
    def from_string(cls, value: Self | str | None) -> Self:
        """Parse a format name; accepts ``.json``-style extensions and aliases.

        ``txt``/``log`` map to ``TEXT`` and ``jsonl``/``ndjson`` map to ``JSON``.
        """
        if isinstance(value, str):
            key = value.strip().lstrip(".").lower()
            value = _FORMAT_ALIASES.get(key, key)
        return super().from_string(value)

    @property
    def extension(self) -> str:
        """Default file extension (with the leading dot) for this format."""
        if self is LogFormat.JSON:
            return ".json"
        if self is LogFormat.XML:
            return ".xml"
        return ".txt"


class LogTarget(CaseInsensitiveEnum):
    """Where a log destination writes to."""

    CONSOLE = "console"
    FILE = "file"
