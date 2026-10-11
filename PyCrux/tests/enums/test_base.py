"""Tests for ``pycrux.enums.base`` — ``BaseEnum`` and ``CaseInsensitiveEnum``."""

from enum import Enum, IntEnum

import pytest

from pycrux.enums import BaseEnum, CaseInsensitiveEnum


class Color(CaseInsensitiveEnum):
    RED = "Red"
    DARK_BLUE = "Dark-Blue"


class Plain(BaseEnum, Enum):
    ONE = "one"
    TWO = "two"


class Level(BaseEnum, IntEnum):
    LOW = 1
    HIGH = 2


# --- BaseEnum.names ------------------------------------------------------------


def test_names_in_definition_order() -> None:
    assert Plain.names() == ["ONE", "TWO"]
    assert Color.names() == ["RED", "DARK_BLUE"]
    assert Level.names() == ["LOW", "HIGH"]


# --- BaseEnum.equals / not_equals ---------------------------------------------


def test_equals_member_value_and_name() -> None:
    assert Plain.ONE.equals(Plain.ONE)
    assert Plain.ONE.equals("one")
    assert Plain.ONE.equals("ONE")
    assert Plain.ONE.equals("  One  ")


def test_equals_hyphen_matches_underscore_name() -> None:
    assert Color.DARK_BLUE.equals("dark-blue")
    assert Color.DARK_BLUE.equals("DARK_BLUE")


def test_equals_rejects_other_members_and_junk() -> None:
    assert not Plain.ONE.equals(Plain.TWO)
    assert not Plain.ONE.equals("two")
    assert not Plain.ONE.equals("")
    assert not Plain.ONE.equals("   ")
    assert not Plain.ONE.equals(None)
    assert not Plain.ONE.equals(1)


def test_equals_works_with_non_string_values() -> None:
    assert Level.LOW.equals("1")
    assert Level.LOW.equals("low")
    assert not Level.LOW.equals("2")


def test_not_equals() -> None:
    assert Plain.ONE.not_equals("two")
    assert Plain.ONE.not_equals(None)
    assert not Plain.ONE.not_equals("one")
    assert not Plain.ONE.not_equals(Plain.ONE)


# --- BaseEnum.equals_any / not_equals_any -------------------------------------


def test_equals_any() -> None:
    assert Plain.ONE.equals_any(["two", "one"])
    assert Plain.ONE.equals_any([Plain.TWO, Plain.ONE])
    assert not Plain.ONE.equals_any(["two", "three"])
    assert not Plain.ONE.equals_any([])


def test_not_equals_any() -> None:
    assert Plain.ONE.not_equals_any(["two", "three"])
    assert Plain.ONE.not_equals_any([])
    assert not Plain.ONE.not_equals_any(["two", "ONE"])


# --- CaseInsensitiveEnum.from_string ------------------------------------------


def test_from_string_matches_value_case_insensitively() -> None:
    assert Color.from_string("red") is Color.RED
    assert Color.from_string("RED") is Color.RED
    assert Color.from_string("  Red  ") is Color.RED


def test_from_string_matches_name_and_hyphenated_name() -> None:
    assert Color.from_string("dark_blue") is Color.DARK_BLUE
    assert Color.from_string("dark-blue") is Color.DARK_BLUE
    assert Color.from_string("DARK-BLUE") is Color.DARK_BLUE


def test_from_string_returns_member_unchanged() -> None:
    assert Color.from_string(Color.RED) is Color.RED


@pytest.mark.parametrize("bad", [None, "", "   ", 5, 1.5, [], object()])
def test_from_string_rejects_empty_or_non_string(bad) -> None:
    with pytest.raises(ValueError, match="expected non-empty string"):
        Color.from_string(bad)


def test_from_string_unknown_value_lists_valid_values() -> None:
    with pytest.raises(ValueError) as exc:
        Color.from_string("green")
    message = str(exc.value)
    assert "Invalid Color" in message
    assert "'green'" in message
    assert "Red" in message and "Dark-Blue" in message


def test_case_insensitive_enum_is_a_str() -> None:
    assert Color.RED == "Red"
    assert isinstance(Color.RED, str)
    assert str(Color.RED) == "Red"
