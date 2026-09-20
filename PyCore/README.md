# PyCore

Self-contained Python core library and CLI: document conversion (markdown, Word, PDF), UTC/TAI time utilities, HTTP-style exceptions, path/I/O helpers, and office/Excel tooling.

## 🚀 Quick Start

cd PyCore
just setup-venv
source venv/bin/activate
just install-packages

just list
just convert -i README.md

For prerequisites and dependency details, see **📋 Prerequisites & Dependencies** and **⚙️ Build & Configuration** below.

### Usage

Document converter (`cli.py`):

python cli.py -h
python cli.py --list
python cli.py -i report.pdf --out report.docx
python cli.py -i notes.docx pdf
python cli.py -i notes.docx -f pdf
just convert -i README.md
just convert -i /path/to/notes.docx md
just convert-to /path/to/notes.docx md

Office tooling (`office/main.py`):

just office --help
just office export path/to/workbook.xlsx -o output_dir/
just office roster list

Time utilities demo:

just time-demo
# or: python -m core.datetime.time

HTTP exceptions:

from core.exceptions import NotFoundException, exception_for_status

raise NotFoundException("User 42 not found")
exc = exception_for_status(404)

### Output

Converted documents are written to `--out` when given, or **next to the input** using a trailing format (`pdf`, `md`, …), `-f` / `--format`, or the default format for that input type:

| Input | Default output |
| ----- | -------------- |
| `.md` / `.markdown` | `.docx` |
| `.pdf` | `.docx` |
| `.docx` | `.md` |

Example: `just convert -i README.md` creates `README.docx` beside `README.md`.

Office `export` writes one NDJSON (or pretty JSON) file per Excel sheet to the output directory (stdout lists each path).

## ✨ Features

- **Document converter** — Markdown, Word (`.docx`), and PDF via `cli.py` and a registry-based converter pipeline
- **Time utilities** — UTC/TAI conversion and leap-second handling via `TimeUtils`
- **HTTP exceptions** — Typed 4xx/5xx exception classes (`ClientException`, `ServerException`, and children)
- **Path & I/O helpers** — `PathUtils`, `FileUtils`, and related utilities under `core/io/`
- **Office tooling** — Excel export and roster CLI under `office/`
- **Excel helpers** — Filename sanitization and type-hint enums in `office/excel/base.py`

## 📋 Prerequisites & Dependencies

- Python `3.12+`
- [Just](https://github.com/casey/just) (optional — task runner for venv, convert, office, etc.)
- **Microsoft Word** (macOS or Windows only) — required for `docx → pdf` via `docx2pdf`

| Source | Purpose |
| ------ | ------- |
| [`requirements.txt`](requirements.txt) | All runtime packages — install with `just install-packages` |

Packages: `leapseconddata`, `python-docx`, `markdown`, `pdf2docx`, `docx2pdf`, `pandas`, `openpyxl`.

### Installing Just

# macOS
brew install just

# Linux
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/bin

## ⚙️ Build & Configuration

### Build

just setup-venv
source venv/bin/activate
just install-packages

No `.env` file is required. Configuration is via CLI flags.

### Supported conversions

| From | To |
| ---- | -- |
| `.md` / `.markdown` | `.docx` |
| `.docx` | `.md` / `.markdown` / `.pdf` |
| `.pdf` | `.docx` |

### Just commands

Run from **PyCore/** (or `just pycore <command>` from the repo root):

| Command | Description |
| ------- | ----------- |
| `just setup-venv` | Create local `venv/` |
| `just install-packages` | Install from `requirements.txt` |
| `just list` | Show supported document conversions |
| `just convert -i FILE pdf` | Convert to a format (trailing argument) |
| `just convert -i FILE -f pdf` | Same, with explicit `--format` |
| `just convert -i FILE --out OUT` | Convert with explicit output path |
| `just convert-to FILE md` | Shorthand: input + target format |
| `just cli-help` | Show `cli.py` help |
| `just office ARGS...` | Run `office/main.py` (export, roster, …) |
| `just time-demo` | Run UTC/TAI time utilities demo |
| `just clean` | Remove virtual environment |
| `just help` | Show PyCore commands |

## 📁 Project Layout

PyCore/
├── cli.py                      # Document converter CLI
├── requirements.txt
├── Justfile
├── core/
│   ├── converter/
│   │   ├── abstract.py         # AbstractConverter base
│   │   ├── registry.py         # Format routing
│   │   ├── markdown.py         # Word → markdown
│   │   └── pdf.py              # Word → PDF
│   ├── datetime/
│   │   └── time.py             # TimeUtils (UTC, TAI, leap seconds)
│   ├── exceptions/             # HTTP-style 4xx/5xx (one class per file)
│   │   ├── base.py
│   │   ├── http.py
│   │   ├── client.py           # ClientException (4xx base)
│   │   ├── server.py           # ServerException (5xx base)
│   │   ├── bad_request.py      # 400 … gateway_timeout.py 504
│   │   └── __init__.py
│   ├── io/
│   │   ├── paths.py            # PathUtils (paths + sys.path)
│   │   ├── io.py               # FileUtils, TextUtils, PlatformUtils
│   │   └── base.py             # LSP / language-server utilities
│   ├── run_state.py            # RunState workflow enum
│   └── utils/
├── office/
│   ├── main.py                 # Excel export & roster CLI
│   ├── excel/base.py           # ExcelUtils, ExcelDataType
│   └── word/converter.py       # Markdown/PDF ↔ Word converters
├── models/                     # Data models (WIP)
└── README.md                   ← you are here

| Module | Purpose |
| ------ | ------- |
| `core/converter/registry.py` | Maps source/dest extensions to converter classes |
| `office/word/converter.py` | Markdown → Word, PDF → Word |
| `core/converter/markdown.py` | Word → markdown |
| `core/converter/pdf.py` | Word → PDF |
| `core/datetime/time.py` | Leap-second-aware UTC/TAI conversions |
| `core/io/paths.py` | PathUtils — URI/path and sys.path helpers |
| `core/exceptions/` | `ClientException`, `ServerException`, and HTTP status subclasses |
| `office/excel/base.py` | Safe filename stems and Excel type enums |
| `office/main.py` | Vestwell-style Excel export and agent roster CLI |

## 🏗️ Architecture

flowchart TB
CLI["cli.py"] --> Reg["registry.get_converter()"]
Reg --> WordConv["office/word/converter.py"]
Reg --> MDConv["core/converter/markdown.py"]
Reg --> PDFConv["core/converter/pdf.py"]
WordConv --> Out["Output file"]
MDConv --> Out
PDFConv --> Out

subgraph core_pkg ["core/"]
Time["datetime/time.py"]
Exc["exceptions/"]
IO["io/paths.py"]
end

subgraph office_pkg ["office/"]
Main["main.py"]
Excel["excel/base.py"]
end

Each converter implements `AbstractConverter` with `source_extensions`, `dest_extensions`, and `convert(source, destination)`.

### Time utilities

from core.datetime.time import TimeUtils

utc_time = TimeUtils.now()
leap_seconds = TimeUtils.get_leap_seconds(utc_time)
tai_time = TimeUtils.to_tai(utc_time)
utc_time = TimeUtils.from_tai(tai_time)

Uses `leapseconddata` for IERS-aligned leap-second offsets.

### HTTP exceptions

from core.exceptions import NotFoundException, exception_for_status, HTTP_EXCEPTIONS

raise NotFoundException()
raise NotFoundException("Resource missing")

exc = exception_for_status(503)  # → ServiceUnavailableException

Hierarchy: `BaseException` → `HTTPException` → `ClientException` / `ServerException` → specific `*Exception` per status code.

## 🧪 Testing

source venv/bin/activate
just list
python cli.py -i README.md --out /tmp/test.docx
just time-demo
just office --help

python -c "from core.exceptions import HTTP_EXCEPTIONS; assert len(HTTP_EXCEPTIONS) == 13"

## 🛠️ Troubleshooting

**`docx → pdf` fails**

- **Cause:** `docx2pdf` requires Microsoft Word on macOS or Windows
- **Fix:** Install Word, or convert via markdown instead

**`Unsupported conversion` error**

- **Cause:** Source and destination extensions are not paired in the registry
- **Fix:** Run `just list` and use a supported pair

**`ModuleNotFoundError: core`**

- **Cause:** Commands run outside `PyCore/` without `PYTHONPATH`
- **Fix:** Run from `PyCore/`, or `source venv/bin/activate` first

| Issue | Fix |
| ----- | --- |
| Missing libraries | `just install-packages` |
| `office/main.py` import errors | Run via `just office` (bootstraps `sys.path`) |

## 📚 References

### In this repository

| README / Link | Description |
| ------------- | ----------- |
| [office/README.md](office/README.md) | Office/Excel export and roster tooling details |

### External Documentation

| Link | Description |
| ---- | ----------- |
| [Just](https://github.com/casey/just) | Task runner used by `Justfile` |
| [python-docx](https://python-docx.readthedocs.io/) | Word read/write |
| [leapseconddata](https://pypi.org/project/leapseconddata/) | Leap second data source |
| [IERS](https://www.iers.org) | Leap second announcements |

## 📄 License

[Add your license here]

## 👤 Author

- **Rohtash Lakra** — [@rslakra](https://github.com/rslakra)
