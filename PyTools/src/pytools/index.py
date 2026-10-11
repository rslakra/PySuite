"""Map legacy monolith paths to current PySuite project locations."""

from __future__ import annotations

from pathlib import Path

# Legacy path fragment → (project folder, current path under repo root)
PROJECT_INDEX: dict[str, tuple[str, str]] = {
    "cli.py": ("PyCore", "PyCore/src/core/cli.py"),
    "core/converter": ("PyCore", "PyCore/src/core/converter"),
    "core/time/time.py": ("PyCore", "PyCore/src/core/datetime/time.py"),
    "core/datetime/time.py": ("PyCore", "PyCore/src/core/datetime/time.py"),
    "learning/": ("PyCademy", "PyCademy/src/pycademy"),
    "office/main.py": ("PyCore", "PyCore/src/office/main.py"),
    "photo_mixer.py": ("PhotoMixer", "PhotoMixer/src/photomixer/cli.py"),
}


def resolve_path(legacy_key: str, repo_root: Path | str | None = None) -> Path:
    """Return absolute path for a legacy key relative to the monorepo root."""
    if legacy_key not in PROJECT_INDEX:
        raise KeyError(f"Unknown legacy path: {legacy_key!r}. Known: {sorted(PROJECT_INDEX)}")

    _, relative = PROJECT_INDEX[legacy_key]
    root = Path(repo_root or Path(__file__).resolve().parents[3])
    return (root / relative).resolve()
