"""Python utilities."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("Amey-PyCrux")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
