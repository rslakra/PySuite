"""Tests for ``pycrux.io.utils.IOUtils``."""

import os
from pathlib import Path

import pytest

import pycrux.io as io_package
import pycrux.io.utils as utils_module
from pycrux.io import IOUtils


@pytest.fixture(autouse=True)
def _restore_root():
    original = IOUtils.CUR_PATH
    yield
    IOUtils.CUR_PATH = original


# --- CUR_PATH / set_root -----------------------------------------------------------------


def test_default_root_is_the_working_directory_at_import_time() -> None:
    assert isinstance(IOUtils.CUR_PATH, Path)
    assert IOUtils.CUR_PATH.is_absolute()


def test_set_root_resolves_the_directory(tmp_path) -> None:
    IOUtils.set_root(tmp_path)
    assert IOUtils.CUR_PATH == tmp_path.resolve()


def test_set_root_accepts_strings_and_expands_user(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    IOUtils.set_root("~")
    assert IOUtils.CUR_PATH == tmp_path.resolve()


def test_set_root_resolves_relative_paths_against_the_cwd(tmp_path, monkeypatch) -> None:
    (tmp_path / "sub").mkdir()
    monkeypatch.chdir(tmp_path)
    IOUtils.set_root("sub")
    assert IOUtils.CUR_PATH == (tmp_path / "sub").resolve()


# --- resolve -----------------------------------------------------------------------------


def test_resolve_relative_path_uses_the_root(tmp_path) -> None:
    IOUtils.set_root(tmp_path)
    assert IOUtils.resolve("data/file.txt") == (tmp_path / "data" / "file.txt").resolve()
    assert IOUtils.resolve(Path("a.txt")) == (tmp_path / "a.txt").resolve()


def test_resolve_absolute_path_ignores_the_root(tmp_path) -> None:
    IOUtils.set_root(tmp_path / "root")
    other = tmp_path / "other" / "x.txt"
    assert IOUtils.resolve(other) == other.resolve()
    assert IOUtils.resolve(str(other)) == other.resolve()


def test_resolve_normalises_dot_segments(tmp_path) -> None:
    IOUtils.set_root(tmp_path)
    assert IOUtils.resolve("a/../b/./c.txt") == (tmp_path / "b" / "c.txt").resolve()


def test_resolve_expands_the_home_directory(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    assert IOUtils.resolve("~/x.txt") == (tmp_path / "x.txt").resolve()


def test_resolve_does_not_require_the_path_to_exist(tmp_path) -> None:
    IOUtils.set_root(tmp_path)
    assert not IOUtils.resolve("nope/missing.txt").exists()


# --- load_env ----------------------------------------------------------------------------


def test_load_env_reads_the_dotenv_file_from_the_root(tmp_path, monkeypatch) -> None:
    pytest.importorskip("dotenv")
    monkeypatch.delenv("PYCRUX_TEST_VALUE", raising=False)
    (tmp_path / ".env").write_text("PYCRUX_TEST_VALUE=from-dotenv\n", encoding="utf-8")
    IOUtils.set_root(tmp_path)

    IOUtils.load_env()

    assert os.environ["PYCRUX_TEST_VALUE"] == "from-dotenv"
    monkeypatch.delenv("PYCRUX_TEST_VALUE")


def test_load_env_custom_filename_does_not_override_existing_values(tmp_path, monkeypatch) -> None:
    pytest.importorskip("dotenv")
    monkeypatch.setenv("PYCRUX_TEST_KEEP", "original")
    monkeypatch.delenv("PYCRUX_TEST_NEW", raising=False)
    (tmp_path / "custom.env").write_text("PYCRUX_TEST_KEEP=changed\nPYCRUX_TEST_NEW=1\n", encoding="utf-8")
    IOUtils.set_root(tmp_path)

    IOUtils.load_env("custom.env")

    assert os.environ["PYCRUX_TEST_KEEP"] == "original"  # python-dotenv does not override by default
    assert os.environ["PYCRUX_TEST_NEW"] == "1"
    monkeypatch.delenv("PYCRUX_TEST_NEW")


def test_load_env_without_a_file_is_a_noop(tmp_path) -> None:
    pytest.importorskip("dotenv")
    IOUtils.set_root(tmp_path)
    IOUtils.load_env()  # must not raise


def test_load_env_without_python_dotenv_raises_a_helpful_error(monkeypatch) -> None:
    monkeypatch.setattr(utils_module, "load_dotenv", None)
    with pytest.raises(ImportError, match=r"pip install PyCrux\[dotenv\]"):
        IOUtils.load_env()


def test_module_imports_without_python_dotenv(reload_without) -> None:
    module = reload_without(utils_module, "dotenv")
    assert module.load_dotenv is None
    with pytest.raises(ImportError, match="python-dotenv is required"):
        module.IOUtils.load_env()


# --- package export -----------------------------------------------------------------------


def test_io_utils_is_exported_from_the_package() -> None:
    assert io_package.IOUtils is IOUtils
    assert utils_module.__all__ == ["IOUtils"]
