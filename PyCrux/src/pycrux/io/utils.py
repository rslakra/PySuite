"""Filesystem and environment helpers with a configurable root directory (stdlib only)."""

from __future__ import annotations

from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # optional dependency: pip install "PyCrux[dotenv]"
    load_dotenv = None  # type: ignore[assignment]

__all__ = ["IOUtils"]


class IOUtils:
    """Filesystem helpers with a configurable root directory."""

    CUR_PATH: Path = Path.cwd()

    @classmethod
    def set_root(cls, root: str | Path) -> None:
        """Set the directory used to resolve relative paths and locate ``.env``."""
        cls.CUR_PATH = Path(root).expanduser().resolve()

    @classmethod
    def load_env(cls, filename: str = ".env") -> None:
        """Load environment variables from ``CUR_PATH / filename`` if present."""
        if load_dotenv is None:
            raise ImportError(
                "python-dotenv is required for load_env(). "
                "Install with: pip install PyCrux[dotenv]"
            )
        load_dotenv(cls.CUR_PATH / filename)

    @classmethod
    def resolve(cls, value: str | Path) -> Path:
        """Return ``value`` as an absolute path, resolved against ``CUR_PATH`` when relative."""
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = cls.CUR_PATH / path
        return path.resolve()
