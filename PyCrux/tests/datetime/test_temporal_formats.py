"""Tests for the base classes in ``pycrux.datetime.temporal`` and ``pycrux.datetime.formats``."""

import pytest

import pycrux.datetime.zones as zones
from pycrux.datetime.formats import Formatter
from pycrux.datetime.temporal import Temporal


def test_temporal_can_be_created() -> None:
    assert isinstance(Temporal(), Temporal)


def test_temporal_equality_and_hash_are_abstract() -> None:
    with pytest.raises(NotImplementedError):
        Temporal() == Temporal()  # noqa: B015
    with pytest.raises(NotImplementedError):
        hash(Temporal())


def test_temporal_subclass_can_implement_the_protocol() -> None:
    class Instant(Temporal):
        def __init__(self, value: int) -> None:
            super().__init__()
            self.value = value

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Instant) and self.value == other.value

        def __hash__(self) -> int:
            return hash(self.value)

    assert Instant(1) == Instant(1)
    assert Instant(1) != Instant(2)
    assert len({Instant(1), Instant(1), Instant(2)}) == 2


def test_formatter_can_be_created_and_format_is_abstract() -> None:
    formatter = Formatter()
    with pytest.raises(NotImplementedError):
        formatter.format("anything")


def test_formatter_subclass_can_implement_format() -> None:
    class Upper(Formatter):
        def format(self, value):
            return str(value).upper()

    assert Upper().format("abc") == "ABC"


def test_zones_module_is_importable() -> None:
    assert zones.__name__ == "pycrux.datetime.zones"
