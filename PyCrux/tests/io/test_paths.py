"""Tests for ``pycrux.io.paths.PathUtils`` and the helpers re-exported from ``pycrux.io``."""

import os
import sys
from pathlib import Path, PurePath, PureWindowsPath

import pytest

import pycrux.io as io_package
import pycrux.io.paths as paths_module
from pycrux.io import PathUtils

posix_only = pytest.mark.skipif(os.name == "nt", reason="POSIX path semantics")


@pytest.fixture
def clean_sys_path(monkeypatch):
    """Let a test modify ``sys.path`` freely."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    return sys.path


# --- uri_to_path ---------------------------------------------------------------------


@posix_only
def test_uri_to_path_decodes_percent_escapes() -> None:
    assert PathUtils.uri_to_path("file:///tmp/a%20b/c.txt") == "/tmp/a b/c.txt"


@posix_only
def test_uri_to_path_normalises_dot_segments() -> None:
    assert PathUtils.uri_to_path("file:///tmp/x/../y/./z.txt") == "/tmp/y/z.txt"


@posix_only
def test_uri_to_path_handles_unicode() -> None:
    assert PathUtils.uri_to_path("file:///tmp/h%C3%A9llo.txt") == "/tmp/héllo.txt"


# --- path_to_uri ---------------------------------------------------------------------


def test_path_to_uri_makes_a_file_uri(tmp_path) -> None:
    uri = PathUtils.path_to_uri(str(tmp_path / "a b.txt"))
    assert uri.startswith("file:///")
    assert uri.endswith("a%20b.txt")


def test_path_to_uri_makes_relative_paths_absolute(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert PathUtils.path_to_uri("rel.txt") == (tmp_path / "rel.txt").absolute().as_uri()


@posix_only
def test_uri_round_trip(tmp_path) -> None:
    original = tmp_path / "sub dir" / "héllo.txt"
    assert PathUtils.uri_to_path(PathUtils.path_to_uri(str(original))) == str(original.absolute())


# --- is_glob_pattern -------------------------------------------------------------------


@pytest.mark.parametrize("pattern", ["*.py", "src/**/*.py", "file?.txt", "[abc].txt", "!negated", "a*"])
def test_is_glob_pattern_true(pattern: str) -> None:
    assert PathUtils.is_glob_pattern(pattern) is True


@pytest.mark.parametrize("pattern", ["", "plain.txt", "src/pkg/module.py", "with space.txt"])
def test_is_glob_pattern_false(pattern: str) -> None:
    assert PathUtils.is_glob_pattern(pattern) is False


# --- get_relative_path -----------------------------------------------------------------


@posix_only
def test_get_relative_path() -> None:
    assert PathUtils.get_relative_path("/a/b/c.txt", "/a") == "b/c.txt"
    assert PathUtils.get_relative_path("/a", "/a/b") == ".."
    assert PathUtils.get_relative_path("/a/b", "/a/b") == "."
    assert PathUtils.get_relative_path("/x/y", "/a/b") == "../../x/y"


def test_get_relative_path_returns_none_across_drives(monkeypatch) -> None:
    monkeypatch.setattr(paths_module, "PurePath", PureWindowsPath)
    assert PathUtils.get_relative_path("C:\\a\\b", "D:\\a") is None


def test_get_relative_path_same_drive_is_not_none(monkeypatch) -> None:
    monkeypatch.setattr(paths_module, "PurePath", PurePath)
    assert PathUtils.get_relative_path(str(Path.cwd() / "x"), str(Path.cwd())) == "x"


# --- ensure_directory_on_sys_path ------------------------------------------------------


def test_ensure_directory_inserts_at_the_front(tmp_path, clean_sys_path) -> None:
    result = PathUtils.ensure_directory_on_sys_path(tmp_path)
    assert result == tmp_path.resolve()
    assert sys.path[0] == str(tmp_path.resolve())


def test_ensure_directory_is_idempotent(tmp_path, clean_sys_path) -> None:
    PathUtils.ensure_directory_on_sys_path(tmp_path)
    PathUtils.ensure_directory_on_sys_path(str(tmp_path))
    assert sys.path.count(str(tmp_path.resolve())) == 1


def test_ensure_directory_does_not_move_an_existing_entry(tmp_path, clean_sys_path) -> None:
    sys.path.append(str(tmp_path.resolve()))
    before = list(sys.path)
    PathUtils.ensure_directory_on_sys_path(tmp_path)
    assert sys.path == before


def test_ensure_directory_resolves_relative_paths(tmp_path, clean_sys_path, monkeypatch) -> None:
    (tmp_path / "child").mkdir()
    monkeypatch.chdir(tmp_path)
    assert PathUtils.ensure_directory_on_sys_path("child") == (tmp_path / "child").resolve()


# --- ensure_package_root_for_file --------------------------------------------------------


def test_ensure_package_root_walks_up_the_given_levels(tmp_path, clean_sys_path) -> None:
    module = tmp_path / "a" / "b" / "mod.py"
    module.parent.mkdir(parents=True)
    module.write_text("", encoding="utf-8")

    assert PathUtils.ensure_package_root_for_file(module, ancestor_levels=1) == (tmp_path / "a" / "b").resolve()
    assert PathUtils.ensure_package_root_for_file(module, ancestor_levels=2) == (tmp_path / "a").resolve()
    assert PathUtils.ensure_package_root_for_file(str(module), ancestor_levels=3) == tmp_path.resolve()
    assert str(tmp_path.resolve()) in sys.path


def test_ensure_package_root_requires_a_keyword_argument(tmp_path) -> None:
    with pytest.raises(TypeError):
        PathUtils.ensure_package_root_for_file(tmp_path / "x.py", 1)  # type: ignore[misc]


# --- package re-exports -----------------------------------------------------------------


def test_package_re_exports() -> None:
    assert io_package.PathUtils is PathUtils
    assert io_package.ensure_directory_on_sys_path is PathUtils.ensure_directory_on_sys_path
    assert io_package.ensure_package_root_for_file is PathUtils.ensure_package_root_for_file
    assert io_package.Path is Path  # the stub class that used to shadow pathlib.Path is gone
    assert set(io_package.__all__) == {
        "IOUtils",
        "PathUtils",
        "ensure_directory_on_sys_path",
        "ensure_package_root_for_file",
        "Path",
    }
