"""Excel helpers: a filename sanitizer (:class:`ExcelUtils`) and the type-hint enum (:class:`ExcelDataType`).

Both are pure Python (standard library only), so importing this module does not need pandas or openpyxl.
"""

from __future__ import annotations

import re
from enum import Enum


class ExcelUtils:
    """Static helpers for turning Excel labels into safe filename stems (no path, no extension)."""

    @staticmethod
    def sanitize_filename(label: str) -> str:
        """
        Turn an Excel sheet name, field name, or similar label into a safe filename stem.

        Steps, in order:

        1. Strip leading and trailing whitespace.
        2. Replace each character in ``< > : " / \\ | ? *`` and each ASCII control character
           (``\\x00``-``\\x1f``, which includes tab and newline) with ``_``.
        3. Collapse each run of the remaining whitespace (e.g. spaces) into a single space, then strip again.
        4. Return ``"sheet"`` if nothing is left.

        Because step 2 runs before step 3, tabs and newlines become ``_``; they are not collapsed to a space.
        Trailing dots and OS-reserved names (e.g. ``CON`` on Windows) are not handled.
        The result is meant to be used as a file stem, e.g. ``f"{sanitize_filename(name)}.json"``.
        """
        # Step 1: strip.
        name = label.strip()
        # Step 2: characters that are reserved or unsafe in filenames, plus control characters.
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
        # Step 3: collapse remaining whitespace runs, then strip again.
        name = re.sub(r"\s+", " ", name).strip()
        # Step 4: never return an empty stem.
        return name or "sheet"


class ExcelDataType(str, Enum):
    """
    Type-hint tokens found in the type-hint row of *Record Test* style sheets.

    That row sits above the real column-header row (the logical column names). Its cells hold a
    data-type keyword per column, such as ``INTEGER`` or ``STRING``.

    The members cover the Excel/VBA-style families (integer/long, single/double, string, boolean,
    variant), plus ``VARCHAR`` (a SQL spelling of string) and ``DATE``, ``TIMESTAMP`` and ``JSON``,
    which are not classic VBA scalar types but are used for Platform Data sheets such as
    ``SampleData.xlsx``.

    The ``str`` mix-in makes each member compare equal to its text, so ``ExcelDataType.STRING == "STRING"``.
    Hints are matched case-sensitively and are not normalised.

    After the class body, ``ExcelDataType.HINT_TOKENS`` holds the set of all member values.
    """

    # Integer / Long — whole numbers
    INTEGER = "INTEGER"
    LONG = "LONG"

    # Single / Double — floating-point (``FLOAT`` is the spelling used on the sample workbook)
    FLOAT = "FLOAT"
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"

    # String — text (``VARCHAR`` is the SQL spelling)
    STRING = "STRING"
    VARCHAR = "VARCHAR"

    # Boolean — true/false
    BOOLEAN = "BOOLEAN"

    # Variant — may hold any value
    VARIANT = "VARIANT"

    # Not classic VBA scalar keywords; used on the Platform Data sample sheets
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"
    JSON = "JSON"


# Set after the class is created, because a plain class attribute would become an enum member.
# Use it to test whether a cell's text is a type hint: ``cell in ExcelDataType.HINT_TOKENS``.
ExcelDataType.HINT_TOKENS = frozenset(m.value for m in ExcelDataType)
