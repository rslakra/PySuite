"""
Platform-agnostic path utilities and ``sys.path`` helpers.

Path and ``sys.path`` helpers (e.g. PoCSuite repo root on ``sys.path``).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path, PurePath


class PathUtils:
    """
    Utilities for platform-agnostic path operations.
    """

    @staticmethod
    def uri_to_path(uri: str) -> str:
        """
        Converts a URI to a file path. Works on both Linux and Windows.

        This method was obtained from https://stackoverflow.com/a/61922504
        """
        try:
            from urllib.parse import unquote, urlparse
            from urllib.request import url2pathname
        except ImportError:
            # backwards compatibility (Python 2)
            from urllib.parse import unquote as unquote_py2
            from urllib.request import url2pathname as url2pathname_py2

            from urlparse import urlparse as urlparse_py2

            unquote = unquote_py2
            url2pathname = url2pathname_py2
            urlparse = urlparse_py2
        parsed = urlparse(uri)
        host = f"{os.path.sep}{os.path.sep}{parsed.netloc}{os.path.sep}"
        path = os.path.normpath(os.path.join(host, url2pathname(unquote(parsed.path))))
        return path

    @staticmethod
    def path_to_uri(path: str) -> str:
        """
        Converts a file path to a file URI (file:///...).
        """
        return str(Path(path).absolute().as_uri())

    @staticmethod
    def is_glob_pattern(pattern: str) -> bool:
        """Check if a pattern contains glob-specific characters."""
        return any(c in pattern for c in "*?[]!")

    @staticmethod
    def get_relative_path(path: str, base_path: str) -> str | None:
        """
        Gets relative path if it's possible (paths should be on the same drive),
        returns `None` otherwise.
        """
        if PurePath(path).drive == PurePath(base_path).drive:
            rel_path = str(PurePath(os.path.relpath(path, base_path)))
            return rel_path
        return None

    @staticmethod
    def ensure_directory_on_sys_path(directory: Path | str) -> Path:
        """
        Insert ``directory`` at the front of ``sys.path`` if it is not already present.

        Returns the resolved directory (useful as package root, e.g. PoCSuite repo root).
        """
        d = Path(directory).resolve()
        s = str(d)
        if s not in sys.path:
            sys.path.insert(0, s)
        return d

    @staticmethod
    def ensure_package_root_for_file(
        module_file: Path | str, *, ancestor_levels: int
    ) -> Path:
        """
        Resolve a directory by walking ``ancestor_levels`` ``.parent`` steps from ``module_file``,
        then ensure it is on ``sys.path``.

        Examples
        --------
        * ``PoCSuite/main.py`` → ``ancestor_levels=1`` → PoCSuite repo root
        * ``tenants/vestwell/foo.py`` → ``ancestor_levels=2`` → PoCSuite repo root
        """
        p = Path(module_file).resolve()
        for _ in range(ancestor_levels):
            p = p.parent
        return PathUtils.ensure_directory_on_sys_path(p)
