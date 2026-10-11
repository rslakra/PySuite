"""Excel-related utilities (safe stems, type-hint enum)."""

from __future__ import annotations

import re
from enum import Enum


class ExcelUtils:
    """Generic helpers for turning Excel labels into safe filenames (no path, no extension)."""

    @staticmethod
    def sanitize_filename(label: str) -> str:
        """
        Turn any Excel sheet name, field name, or similar label into a safe filename string.

        Strips; replaces reserved/problematic characters with ``_``; collapses whitespace.
        Result is typically used as a file stem (e.g. ``{sanitize_filename(name)}.json``).
        """
        name = label.strip()
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name or "sheet"


class ExcelDataType(str, Enum):
    """
    Row-0 type hints on *Record Test* style sheets (before the real column header row).

    Mirrors common Excel/VBA-style families (integer/long, single/double, string, boolean,
    variant). ``DATE``, ``TIMESTAMP``, and ``JSON`` are included because they appear in
    ``Sample Data For Invisible.xlsx`` and similar Vestwell exports.

    String mix-in (``str, Enum``) makes each member compare and format like its cell text.
    """

    # Integer / Long — whole numbers
    INTEGER = "INTEGER"
    LONG = "LONG"

    # Single / Double — floating-point (``FLOAT`` is used on the sample workbook)
    FLOAT = "FLOAT"
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"

    # String — text
    STRING = "STRING"
    VARCHAR = "VARCHAR"

    # Boolean
    BOOLEAN = "BOOLEAN"

    # Variant — may hold any value
    VARIANT = "VARIANT"

    # Used on Platform Data sample sheets (not classic Excel scalar keywords)
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"
    JSON = "JSON"


ExcelDataType.HINT_TOKENS = frozenset(m.value for m in ExcelDataType)
