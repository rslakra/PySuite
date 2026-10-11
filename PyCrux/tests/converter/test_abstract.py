"""Tests for ``pycrux.converter.abstract.AbstractConverter``."""

from pathlib import Path

import pytest

import pycrux.converter as converter_package
from pycrux.converter import AbstractConverter


def test_cannot_instantiate_the_abstract_class() -> None:
    with pytest.raises(TypeError):
        AbstractConverter()  # type: ignore[abstract]


def test_subclass_without_convert_cannot_be_instantiated() -> None:
    class Incomplete(AbstractConverter):
        source_extensions = frozenset({"a"})
        dest_extensions = frozenset({"b"})

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_concrete_subclass_works() -> None:
    class Copy(AbstractConverter):
        source_extensions = frozenset({"txt"})
        dest_extensions = frozenset({"bak"})

        def convert(self, source: Path, destination: Path) -> None:
            destination.write_text(source.read_text())

    converter = Copy()
    assert isinstance(converter, AbstractConverter)
    assert Copy.source_extensions == {"txt"} and Copy.dest_extensions == {"bak"}


def test_convert_contract_receives_paths(tmp_path) -> None:
    class Copy(AbstractConverter):
        source_extensions = frozenset({"txt"})
        dest_extensions = frozenset({"bak"})

        def convert(self, source: Path, destination: Path) -> None:
            destination.write_text(source.read_text())

    src, dst = tmp_path / "a.txt", tmp_path / "a.bak"
    src.write_text("hello")
    Copy().convert(src, dst)
    assert dst.read_text() == "hello"


def test_package_exports_only_the_abstract_class() -> None:
    assert converter_package.__all__ == ["AbstractConverter"]
    assert converter_package.AbstractConverter is AbstractConverter
