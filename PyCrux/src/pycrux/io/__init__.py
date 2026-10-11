"""I/O utilities — path, file, and text helpers.

Only the dependency-free helpers (``paths`` and ``utils``) are re-exported here. ``base``, ``buffers`` and
``symbols`` need third-party packages (``solidlsp`` and friends), so import them explicitly, e.g.
``from pycrux.io.base import FileUtils``.
"""

from .paths import Path, PathUtils
from .utils import IOUtils

# Module-level aliases for the ``sys.path`` helpers
ensure_directory_on_sys_path = PathUtils.ensure_directory_on_sys_path
ensure_package_root_for_file = PathUtils.ensure_package_root_for_file

__all__ = [
    "IOUtils",
    "PathUtils",
    "ensure_directory_on_sys_path",
    "ensure_package_root_for_file",
    "Path",
]
