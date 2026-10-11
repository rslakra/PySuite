"""Tests for ``pycrux.enums.os.OS``."""

import pytest

from pycrux.enums import OS


def test_members_and_values() -> None:
    assert OS.ANDROID.value == "Android"
    assert OS.IOS.value == "iOS"
    assert OS.LINUX.value == "Linux"
    assert OS.MACOS.value == "MacOS"
    assert OS.WINDOWS.value == "Windows"
    assert OS.OTHER.value == "Other"


def test_names() -> None:
    assert OS.names() == ["ANDROID", "IOS", "LINUX", "MACOS", "WINDOWS", "OTHER"]


def test_from_string() -> None:
    assert OS.from_string("macos") is OS.MACOS
    assert OS.from_string("iOS") is OS.IOS
    assert OS.from_string("IOS") is OS.IOS
    assert OS.from_string(OS.LINUX) is OS.LINUX


@pytest.mark.parametrize("bad", [None, "", "beos"])
def test_from_string_rejects_invalid(bad) -> None:
    with pytest.raises(ValueError):
        OS.from_string(bad)


def test_equality_helpers() -> None:
    assert OS.WINDOWS.equals("Windows")
    assert OS.WINDOWS.equals("windows")
    assert OS.WINDOWS.not_equals("linux")
    assert OS.MACOS.equals_any(["linux", "macos"])
    assert OS.ANDROID.not_equals_any(["ios", "windows"])
