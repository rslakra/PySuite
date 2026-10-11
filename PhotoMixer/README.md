# PhotoMixer

Blend a foreground image onto a background with configurable opacity and blend modes — CLI tool built on Pillow, numpy, and scipy.

## 🚀 Quick Start

```bash
cd PhotoMixer
just install-packages
source venv/bin/activate

just run images/original/bg.jpg images/original/fg.jpg
```

For dependency details, see **📋 Prerequisites & Dependencies** below.

### Usage

```bash
just run bg.jpg fg.jpg
just run bg.jpg fg.jpg output=result.jpg blend_mode=multiply opacity=0.9
python -m photomixer.cli -b bg.jpg -f fg.jpg -m overlay -p 0.7 -o result.jpg
photomixer -b bg.jpg -f fg.jpg   # after pip install -e .
```

From the repo root: `just photomixer run bg.jpg fg.jpg`

### Output

Mixed images are saved to `--output` / `-o`, or by default:

```
images/mixed/mixed_<bg>_<fg>.jpg
```

## ✨ Features

- **CLI interface** — `--background`, `--foreground`, optional output, blend mode, opacity
- **Automatic resizing** — foreground scaled to fit the background
- **Blend modes** — `normal`, `multiply`, `screen`, `overlay`
- **Opacity control** — foreground transparency from `0.0` to `1.0`
- **Just tasks** — `just setup`, `just run`, `just clean`

## 📋 Prerequisites & Dependencies

- Python `3.12+`
- [Just](https://github.com/casey/just) (optional)

| Source | Purpose |
| ------ | ------- |
| [`requirements.txt`](requirements.txt) | Editable install (`-e .`) — Pillow, numpy, scipy via `pyproject.toml` |

Packages: `Pillow>=10`, `numpy>=1.24`, `scipy>=1.10`.

## ⚙️ Build & Configuration

### Build

```bash
cd PhotoMixer
just install-packages    # venv + pip install -e .
source venv/bin/activate
```

Library code lives under **`src/photomixer/`**. After editable install, run with `python -m photomixer.cli` or the `photomixer` console script.

No environment variables are required. All options are CLI flags.

### Just commands

Run from **PhotoMixer/** (or `just photomixer <command>` from repo root):

| Command | Description |
| ------- | ----------- |
| `just install-packages` | Create `venv/` and `pip install -e .` |
| `just setup` | Alias for `install-packages` |
| `just run BG FG [options]` | Blend two images |
| `just clean` | Remove virtual environment |
| `just help` | Show commands and examples |

**Just option syntax** (note underscore vs hyphen):

| Just argument | Python flag |
| ------------- | ------------- |
| `output=path.jpg` | `--output path.jpg` |
| `blend_mode=multiply` | `--blend-mode multiply` |
| `opacity=0.9` | `--opacity 0.9` |

### CLI reference

| Flag | Description | Default |
| ---- | ----------- | ------- |
| `-b` / `--background` | Background image path | required |
| `-f` / `--foreground` | Foreground image path | required |
| `-o` / `--output` | Output file path | `images/mixed/mixed_<bg>_<fg>.jpg` |
| `-m` / `--blend-mode` | `normal`, `multiply`, `screen`, `overlay` | `normal` |
| `-p` / `--opacity` | Foreground opacity `0.0`–`1.0` | `0.8` |

## 📁 Project Layout

```
PhotoMixer/
├── src/
│   └── photomixer/
│       ├── cli.py        # CLI entry point
│       └── __init__.py
├── photo_mixer.py        # backward-compatible shim
├── pyproject.toml
├── requirements.txt      # -e .
├── Justfile
└── README.md             ← you are here
```

## 🏗️ Architecture

```mermaid
flowchart LR
  CLI["photomixer.cli"] --> Load["Load BG + FG"]
  Load --> Resize["Resize foreground"]
  Resize --> Blend["Blend + opacity"]
  Blend --> Save["Write JPEG/PNG"]
```

The script loads both images with Pillow, resizes the foreground, applies the selected blend mode and opacity, then writes the composite to disk.

## 🧪 Testing

```bash
just run bg.jpg fg.jpg output=/tmp/test.jpg
python -m photomixer.cli --help
```

Visually inspect the output image for correct blending and sizing.

## 🛠️ Troubleshooting

**`ModuleNotFoundError: PIL`**

- **Cause:** Dependencies not installed
- **Fix:** `just install-packages` or `pip install -e .`

**Just `blend_mode` vs Python `--blend-mode`**

- **Cause:** Just passes `blend_mode=` (underscore); the Python CLI uses hyphens
- **Fix:** Use `blend_mode=` in Just recipes — the Justfile maps it automatically

| Issue | Fix |
| ----- | --- |
| Output directory missing | Script creates parent dirs or use an existing path |
| Foreground too large/small | Adjust source images; resizing is automatic |

## 📚 References

### In this repository

| README / Link | Description |
| ------------- | ----------- |
| [PySuite (root)](../README.md) | Monorepo index |

### External Documentation

| Link | Description |
| ---- | ----------- |
| [Pillow](https://pillow.readthedocs.io/) | Python Imaging Library |
| [Just](https://github.com/casey/just) | Task runner |

## 📄 License

[Add your license here]

## 👤 Author

- **Rohtash Lakra** — [@rslakra](https://github.com/rslakra)
