# pycrux.threads

Thread-local, stackable context variables — import from `pycrux.threads` after installing [PyCrux](../../../README.md).

## 🚀 Quick Start

```python
from pycrux.threads import ContextStack

c = ContextStack()

c.foo = "foo"
with c:
    assert c.foo == "foo"   # inherited from the parent context

    c.foo = "bar"           # visible only inside this block
    assert c.foo == "bar"

assert c.foo == "foo"
```

Public types: `Context`, `ContextStack`, `StackUnderflow` (also available as `ContextStack.StackUnderflow`).

## ✨ Features

- **`ContextStack`** — thread-local stack; attribute access goes to the top context
- **Scoped overrides** — `push()` / `pop()` or `with c:` restore previous values on exit
- **Inheritance** — lookups fall through to parent contexts and finally to `c.base`
- **`StackUnderflow`** — raised when popping the last context

## 📋 Prerequisites & Dependencies

- **PyCrux** / editable `pycrux` install
- **stdlib only** (`threading`)

| File | Type | Depends on |
| ---- | ---- | ---------- |
| [`contexts.py`](contexts.py) | `Context`, `ContextStack`, `StackUnderflow` | stdlib |

## ⚙️ Build & Configuration

No separate build — part of the `pycrux` package. Develop via [PyCrux](../../../README.md):

```bash
make setup && make test
```

## 📁 Project Layout

```
threads/
├── __init__.py         # public exports
├── contexts.py
└── README.md           ← you are here
```

## 🏗️ Architecture

| Member | Role |
| ------ | ---- |
| `ContextStack.push()` | Add a child context of the current top; returns it |
| `ContextStack.pop()` | Remove the top context; `StackUnderflow` if only one is left |
| `ContextStack.base` | Root context shared by every level |
| `c[-1]`, `c[0]` … | Index contexts relative to the top (`c[-1]` is the parent of the current context) |
| `len(c)` | Number of contexts on the stack (starts at 1) |
| `dir(c)` | All attribute names visible across the stack |

- `del c.attr` removes it from the **current** context only, so an inherited value shows through again.
- Each thread has its own stack.

## 🧪 Testing

```bash
cd ../../.. && make test
```

| Test file | Covers |
| --------- | -------- |
| [`test_context.py`](../../../tests/test_context.py) | push/pop, `with`, delete, inheritance, `base`, `len`, `dir`, underflow |

See [PyCrux › Testing](../../../README.md#-testing).

## 🛠️ Troubleshooting

| Issue | Fix |
| ----- | --- |
| `AttributeError` on read | Attribute not set in any context on the stack |
| `StackUnderflow` | More `pop()` calls than `push()` calls |

## 📚 References

### In this repository

| README | Description |
| ------ | ----------- |
| [PyCrux](../../../README.md) | Package root, library map, build and tests |
| [PyCrux › Testing](../../../README.md#-testing) | Test layout |

## 📄 License

MIT — see [LICENSE](../../../LICENSE).

## 👤 Author

- **Rohtash Lakra** — [@rslakra](https://github.com/rslakra)
