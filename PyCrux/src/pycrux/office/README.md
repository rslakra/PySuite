# pycrux.office — Excel helpers and Word converters

`pycrux.office` is the office-document part of PyCrux. It contains:

- **`excel/`** — small Excel helpers (safe filename stems, type-hint enum). Standard library only.
- **`word/`** — Word converters (Markdown → Word, PDF → Word) used by `pycrux.converter` and the `pycrux-convert` CLI.

## Package layout

Paths are relative to the **PyCrux** project root.

```
src/pycrux/office/
├── __init__.py          # package docstring only
├── README.md            # this file
├── excel/
│   ├── __init__.py      # re-exports ExcelDataType, ExcelUtils
│   └── base.py          # ExcelUtils, ExcelDataType
└── word/
    ├── __init__.py      # intentionally empty (avoids a circular import)
    └── converter.py     # Markdown2WordConverter, Pdf2WordConverter
```

Tests live in `tests/office/excel/` and `tests/office/word/`.

## Install

Run from the **PyCrux** project root.

```shell
make setup                        # .venv + editable install with every dev extra
# or, manually:
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[convert]"       # python-docx, markdown, pdf2docx, docx2pdf (Word converters)
pip install -e ".[all]"           # everything
```

| Extra | Packages | Needed for |
|-------|----------|------------|
| `convert` | `python-docx`, `markdown`, `pdf2docx`, `docx2pdf` | `word/converter.py` |

`excel/` needs no extra.

## `excel` — `pycrux.office.excel`

```python
from pycrux.office.excel import ExcelDataType, ExcelUtils
```

| Name | Description |
|------|-------------|
| `ExcelUtils.sanitize_filename(label)` | Strips the label, replaces reserved characters (`<>:"/\|?*`) and control characters (including tab and newline) with `_`, then collapses the remaining whitespace. Returns `"sheet"` if the result is empty. Result is a file stem (no path, no extension). Trailing dots and OS-reserved names (e.g. `CON` on Windows) are not handled. |
| `ExcelDataType` | `str`-based `Enum` of the type hints in the row above the real header row of *Record Test* sheets: `INTEGER`, `LONG`, `FLOAT`, `SINGLE`, `DOUBLE`, `STRING`, `VARCHAR` (SQL spelling), `BOOLEAN`, `VARIANT`, `DATE`, `TIMESTAMP`, `JSON`. Each member compares equal to its text, e.g. `ExcelDataType.STRING == "STRING"`. |
| `ExcelDataType.HINT_TOKENS` | `frozenset` of all member values, for checking whether a cell is a type hint. It is case-sensitive: `"integer"` is not a token. It is set after the class is created, so type checkers may not see it. |

```python
ExcelUtils.sanitize_filename("Field Values: Guide/2026")   # 'Field Values_ Guide_2026'
"INTEGER" in ExcelDataType.HINT_TOKENS                      # True
"integer" in ExcelDataType.HINT_TOKENS                      # False (case-sensitive)
```

## `word` — `pycrux.office.word.converter`

Both classes extend `pycrux.converter.abstract.AbstractConverter` and are registered in `pycrux.converter.registry`.

| Class | Source → destination | Requires |
|-------|----------------------|----------|
| `Markdown2WordConverter` | `md`, `markdown` → `docx` | `python-docx`, `markdown` |
| `Pdf2WordConverter` | `pdf` → `docx` | `pdf2docx` |

- `convert(source, destination)` creates the destination's parent directories.
- The optional libraries are imported with `try/except`. Importing the module, and listing conversions, works without them. A missing library raises `ImportError` only when a conversion runs.
- `Markdown2WordConverter` handles headings (`#`–`######`), bullet and numbered lists, and plain paragraphs. Code-fence lines (```` ``` ````) are skipped.
- `word/__init__.py` re-exports nothing on purpose: `converter` imports `pycrux.converter`, whose registry imports this package, so an eager import would be circular. Import from `pycrux.office.word.converter` directly.

For command-line use, see `pycrux-convert` (`pycrux.cli:main`).
