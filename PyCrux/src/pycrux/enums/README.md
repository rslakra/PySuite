# pycrux.enums

Enumerations for deployment environment, devices, OS, and byte sizes — import from `pycrux.enums` after installing [Amey-PyCrux](../../../README.md).

## 🚀 Quick Start

```python
from pycrux.enums import DeviceType, EnvType, OS, SizeUnit

EnvType.from_string("staging")   # EnvType.STAGING
DeviceType.from_string("mobile") # DeviceType.MOBILE
SizeUnit.format_bytes(2048)      # "2.00 KB"
OS.from_string("macos")          # OS.MACOS
```

Public types: `BaseEnum`, `CaseInsensitiveEnum`, `DeviceType`, `EnvType`, `OS`, `RunState`, `SizeUnit`.

## ✨ Features

- **`CaseInsensitiveEnum`** — string enums with `from_string`, hyphen/underscore name matching
- **`EnvType`** — deployment keys and aliases (`staging` → `stg`)
- **`SizeUnit`** — binary IEC byte multipliers and `format_bytes`
- **`DeviceType` / `OS`** — case-insensitive device and platform enums
- **Shared helpers** — `equals`, `equals_any`, `names()` via `BaseEnum` mixin

## 📋 Prerequisites & Dependencies

- **Amey-PyCrux** / editable `pycrux` install
- **stdlib only** — `EnvType` and `SizeUnit` have no internal enum dependencies

| File | Type | Depends on |
| ---- | ---- | ---------- |
| [`base.py`](base.py) | `BaseEnum`, `CaseInsensitiveEnum` | stdlib |
| [`env_type.py`](env_type.py) | `EnvType` | stdlib |
| [`size_unit.py`](size_unit.py) | `SizeUnit` | stdlib (`IntEnum`) |
| [`device_type.py`](device_type.py) | `DeviceType` | `CaseInsensitiveEnum` |
| [`os.py`](os.py) | `OS` | `CaseInsensitiveEnum` |
| [`run_state.py`](run_state.py) | `RunState` (`idle`, `queued`, `running`, `paused`, `skipped`, `completed`, `failed`) | stdlib (`str`, `Enum`) |

## ⚙️ Build & Configuration

No separate build — part of `pycrux` package. Develop via [PyCrux](../../../README.md):

```bash
make setup && make test
```

## 📁 Project Layout

```
enums/
├── __init__.py         # public exports
├── base.py
├── env_type.py
├── size_unit.py
├── device_type.py
├── os.py
└── README.md           ← you are here
```

## 🏗️ Architecture

### Shared helpers (`BaseEnum`)

Mixin for string-style enums — mix **before** `Enum` / `StrEnum` / `IntEnum`.

| Method | Role |
| ------ | ---- |
| `names()` | Member names in definition order |
| `equals(other)` | Same member, value, or name (case-insensitive) |
| `not_equals(other)` | Inverse of `equals` |
| `equals_any(others)` | True if any list item matches |
| `not_equals_any(others)` | True if none match |

`equals_any` / `not_equals_any` take a **list**, not `*args`.

### Case-insensitive string enums (`CaseInsensitiveEnum`)

- Match case-insensitively on **value** or **name**
- Hyphens in input match underscores in names (`foo-bar` → `FOO_BAR`)
- Existing member returned unchanged
- Invalid/empty input → `ValueError`

#### `DeviceType`

| Member | Value |
| ------ | ----- |
| `DESKTOP` | `Desktop` |
| `MOBILE` | `Mobile` |
| `TABLET` | `Tablet` |
| `TV` | `Tv` |

```python
DeviceType.from_string("mobile") is DeviceType.MOBILE
DeviceType.MOBILE.equals("MOBILE")
DeviceType.MOBILE.equals_any(["tablet", "mobile"])
```

#### `OS`

| Member | Value |
| ------ | ----- |
| `ANDROID` | `Android` |
| `IOS` | `iOS` |
| `LINUX` | `Linux` |
| `MACOS` | `MacOS` |
| `WINDOWS` | `Windows` |
| `OTHER` | `Other` |

```python
OS.from_string("macos") is OS.MACOS
OS.MACOS.equals_any(["linux", "macos"])
```

### `EnvType` (standalone)

Deployment environment — **does not** use `BaseEnum`. `from_string` logs and returns `None` for empty/unknown input.

| Member | Canonical key | Aliases |
| ------ | ------------- | ------- |
| `LOCAL` | `local` | |
| `DEV` | `dev` | `develop`, `development` |
| `PROD` | `prod` | `production`, `live` |
| `QA` | `qa` | |
| `STAGING` | `stg` | `stage`, `staging` |
| `TEST` | `test` | `testing` |
| `UAT` | `uat` | |

```python
EnvType.from_string("staging") is EnvType.STAGING
str(EnvType.STAGING)           # "stg"
EnvType.STAGING.env_type       # "stg"
```

### `SizeUnit` (standalone)

Binary (IEC) multipliers as `IntEnum` — compares to integers (`SizeUnit.KB == 1024`).

| Member | Bytes |
| ------ | ----- |
| `B` | 1 |
| `KB` | 1024 |
| `MB` | 1024² |
| `GB` | 1024³ |
| `TB` | 1024⁴ |

```python
SizeUnit.from_string("mb") is SizeUnit.MB
SizeUnit.MB.from_bytes(2048)   # 2.0
SizeUnit.format_bytes(2048)    # "2.00 KB"
```

`format_bytes`: B below 1 KiB, then KB/MB/GB/TB with two decimal places.

### Adding a type

- **Case-insensitive string enum:** subclass `CaseInsensitiveEnum`, declare members only
- **Independent enum:** stdlib `Enum` / `IntEnum`, helpers on the class — do not import `base.py`
- Re-export from [`__init__.py`](__init__.py)
- Add tests in [`tests/test_enums.py`](../../../tests/test_enums.py) or dedicated module

## 🧪 Testing

```bash
cd ../../.. && make test
```

| Test file | Covers |
| --------- | -------- |
| [`test_env_type.py`](../../../tests/test_env_type.py) | `EnvType` |
| [`test_enums.py`](../../../tests/test_enums.py) | `DeviceType`, `OS`, `SizeUnit` |

See [PyCrux › Testing](../../../README.md#-testing).

## 🛠️ Troubleshooting

| Issue | Fix |
| ----- | --- |
| `from_string` returns `None` (`EnvType`) | Unknown alias — check canonical keys table above |
| `ValueError` from `CaseInsensitiveEnum` | Invalid or empty string |
| Circular import adding enum | Keep `EnvType`/`SizeUnit` standalone; don't import `base` from them |

## 📚 References

### In this repository

| README | Description |
| ------ | ----------- |
| [PyCrux](../../../README.md) | Package root, library map, build and tests |
| [PyCrux › Testing](../../../README.md#-testing) | Test layout |

### External Documentation

| Link | Description |
| ---- | ----------- |
| [Python Enum](https://docs.python.org/3/library/enum.html) | stdlib enums |

## 📄 License

MIT — see [LICENSE](../../../LICENSE).

## 👤 Author

- **Rohtash Lakra** — [@rslakra](https://github.com/rslakra)
