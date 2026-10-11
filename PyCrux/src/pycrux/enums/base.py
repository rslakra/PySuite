"""Shared enum helpers and case-insensitive string enums."""

from __future__ import annotations

from enum import StrEnum
from typing import Self


class BaseEnum:
    """Reusable helpers for project enums.

    Mix this in *before* ``Enum`` / ``StrEnum`` / ``IntEnum``.
    """

    @classmethod
    def names(cls) -> list[str]:
        """Return all enum member names in definition order."""
        return [member.name for member in cls]  # type: ignore[not-iterable]

    def equals(self, other: object) -> bool:
        """Return True if ``other`` is this member, its value, or its name."""
        if isinstance(other, type(self)):
            return self is other
        if not isinstance(other, str) or not other.strip():
            return False
        normalized = other.strip().lower()
        return (
            str(self.value).lower() == normalized
            or self.name.lower() == normalized.replace("-", "_")
        )

    def not_equals(self, other: object) -> bool:
        """Return True if ``other`` is not this member."""
        return not self.equals(other)

    def equals_any(self, others: list[object]) -> bool:
        """Return True if this member matches any value in ``others``."""
        return any(self.equals(item) for item in others)

    def not_equals_any(self, others: list[object]) -> bool:
        """Return True if this member matches none of the values in ``others``."""
        return not self.equals_any(others)


class CaseInsensitiveEnum(BaseEnum, StrEnum):
    """String enum with case-insensitive ``from_string`` parsing.

    Also inherits :meth:`names`, :meth:`equals`, :meth:`not_equals`,
    :meth:`equals_any`, and :meth:`not_equals_any` from :class:`BaseEnum`.
    """

    @classmethod
    def from_string(cls, value: Self | str | None) -> Self:
        """Parse a member value or name (case-insensitive).

        Hyphens in the input are treated as underscores when matching names
        (``foo-bar`` matches ``FOO_BAR``). If ``value`` is already a member of
        this enum, it is returned unchanged.
        """
        if isinstance(value, cls):
            return value
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Invalid {cls.__name__}: expected non-empty string, got {value!r}"
            )

        normalized = value.strip()
        lowered = normalized.lower()
        for member in cls:
            if member.value.lower() == lowered:
                return member
            if member.name.lower() == lowered.replace("-", "_"):
                return member
        valid = ", ".join(member.value for member in cls)
        raise ValueError(
            f"Invalid {cls.__name__}: {value!r}. Valid values are: {valid}"
        )
