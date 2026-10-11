"""Binary (IEC) data-size units (stdlib only — no project imports)."""

from __future__ import annotations

from enum import IntEnum, unique


@unique
class SizeUnit(IntEnum):
    """
    Size units as byte multipliers (1024-based).

    Use :meth:`from_bytes` on a unit member, or class helpers ``to_kb`` / ``to_mb`` /
    :meth:`format_bytes` for human-readable output from a raw byte count.
    """

    B = 1
    KB = 1024
    MB = 1024**2
    GB = 1024**3
    TB = 1024**4

    @classmethod
    def names(cls) -> list[str]:
        """Return all enum member names in definition order."""
        return [member.name for member in cls]

    @classmethod
    def from_string(cls, value: SizeUnit | str | None) -> SizeUnit | None:
        """Parse a unit name such as ``KB`` or ``mb`` into a :class:`SizeUnit`.

        If ``value`` is already a :class:`SizeUnit`, it is returned unchanged.
        Returns ``None`` when the value is empty or unrecognized.
        """
        if isinstance(value, cls):
            return value
        if not isinstance(value, str) or not value.strip():
            return None
        key = value.strip().upper()
        try:
            return cls[key]
        except KeyError:
            return None

    def from_bytes(self, size_bytes: int) -> float:
        """Convert ``size_bytes`` into this unit (e.g. ``SizeUnit.MB.from_bytes(2048)``)."""
        return SizeUnit.normalize_bytes(size_bytes) / self.value

    @classmethod
    def normalize_bytes(cls, size_bytes: int) -> int:
        return max(0, int(size_bytes))

    @classmethod
    def to_bytes(cls, size_bytes: int) -> int:
        return cls.normalize_bytes(size_bytes)

    @classmethod
    def to_kb(cls, size_bytes: int) -> float:
        return cls.KB.from_bytes(size_bytes)

    @classmethod
    def to_mb(cls, size_bytes: int) -> float:
        return cls.MB.from_bytes(size_bytes)

    @classmethod
    def to_gb(cls, size_bytes: int) -> float:
        return cls.GB.from_bytes(size_bytes)

    @classmethod
    def to_tb(cls, size_bytes: int) -> float:
        return cls.TB.from_bytes(size_bytes)

    @classmethod
    def format_bytes(cls, size_bytes: int) -> str:
        """
        Human-readable size for log lines — avoids ``0.00 MB`` for small checkpoints.

        Uses B below 1 KiB, then KB / MB / GB / TB with two decimal places.
        """
        n = cls.normalize_bytes(size_bytes)
        if n < cls.KB:
            return f"{n} B"
        if n < cls.MB:
            return f"{cls.KB.from_bytes(n):.2f} KB"
        if n < cls.GB:
            return f"{cls.MB.from_bytes(n):.2f} MB"
        if n < cls.TB:
            return f"{cls.GB.from_bytes(n):.2f} GB"
        return f"{cls.TB.from_bytes(n):.2f} TB"
