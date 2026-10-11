"""Tests for ``pycrux.enums.device_type.DeviceType``."""

import pytest

from pycrux.enums import DeviceType


def test_members_and_values() -> None:
    assert DeviceType.DESKTOP.value == "Desktop"
    assert DeviceType.MOBILE.value == "Mobile"
    assert DeviceType.TABLET.value == "Tablet"
    assert DeviceType.TV.value == "Tv"


def test_names() -> None:
    assert DeviceType.names() == ["DESKTOP", "MOBILE", "TABLET", "TV"]


def test_from_string() -> None:
    assert DeviceType.from_string("mobile") is DeviceType.MOBILE
    assert DeviceType.from_string("TABLET") is DeviceType.TABLET
    assert DeviceType.from_string("tv") is DeviceType.TV
    assert DeviceType.from_string(DeviceType.TV) is DeviceType.TV


@pytest.mark.parametrize("bad", [None, "", "watch"])
def test_from_string_rejects_invalid(bad) -> None:
    with pytest.raises(ValueError):
        DeviceType.from_string(bad)


def test_equality_helpers() -> None:
    assert DeviceType.MOBILE.equals("mobile")
    assert DeviceType.MOBILE.equals("MOBILE")
    assert DeviceType.MOBILE.not_equals("desktop")
    assert DeviceType.MOBILE.equals_any(["tablet", "mobile"])
    assert DeviceType.MOBILE.not_equals_any(["desktop", "tv"])
