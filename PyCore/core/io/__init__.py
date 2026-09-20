"""I/O utilities — path, file, and text helpers."""

from core.io.paths import PathUtils

# Module-level aliases (formerly core/utils/ioutils.py)
ensure_directory_on_sys_path = PathUtils.ensure_directory_on_sys_path
ensure_package_root_for_file = PathUtils.ensure_package_root_for_file

__all__ = [
    "PathUtils",
    "ensure_directory_on_sys_path",
    "ensure_package_root_for_file",
]
