"""Tests for ``pycrux.datetime.time`` — ``TimeUtils``, the placeholder classes and the demo.

``LeapSecondData.from_standard_source()`` reads (or downloads) the IERS leap-second list, so most tests
replace it with a deterministic fake that mirrors the real API (``tai_offset``, ``to_tai``,
``tai_to_utc``); the last tests use the real library and are skipped when it cannot load data.
"""

import importlib
from datetime import datetime, timedelta, timezone

import pytest
from leapseconddata import LeapSecondData, tai

import pycrux.datetime as datetime_package
import pycrux.datetime.time as time_module
from pycrux.datetime import DateTimeUtils, DateUtils, TimeUtils

UTC = timezone.utc


class FakeLeapSecondData:
    """Stand-in with a fixed TAI-UTC offset of 37 seconds."""

    OFFSET = timedelta(seconds=37)
    seen_tai_inputs: list[datetime] = []
    seen_offset_inputs: list[datetime] = []

    @classmethod
    def from_standard_source(cls) -> "FakeLeapSecondData":
        return cls()

    def tai_offset(self, when: datetime) -> timedelta:
        FakeLeapSecondData.seen_offset_inputs.append(when)
        return self.OFFSET

    def to_tai(self, when: datetime) -> datetime:
        return (when + self.OFFSET).replace(tzinfo=tai)

    def tai_to_utc(self, when: datetime) -> datetime:
        FakeLeapSecondData.seen_tai_inputs.append(when)
        return (when - self.OFFSET).replace(tzinfo=UTC)


@pytest.fixture(autouse=True)
def _fake_leap_seconds(monkeypatch):
    FakeLeapSecondData.seen_tai_inputs = []
    FakeLeapSecondData.seen_offset_inputs = []
    monkeypatch.setattr(time_module, "LeapSecondData", FakeLeapSecondData)


# --- now ----------------------------------------------------------------------------


def test_now_is_timezone_aware_utc() -> None:
    before = datetime.now(tz=UTC)
    value = TimeUtils.now()
    after = datetime.now(tz=UTC)
    assert value.tzinfo is not None and value.utcoffset() == timedelta(0)
    assert before <= value <= after


# --- get_leap_seconds ---------------------------------------------------------------


def test_get_leap_seconds_returns_total_offset() -> None:
    assert TimeUtils.get_leap_seconds(datetime(2025, 1, 1, tzinfo=UTC)) == 37


def test_get_leap_seconds_since_1972_subtracts_initial_ten() -> None:
    assert TimeUtils.get_leap_seconds(datetime(2025, 1, 1, tzinfo=UTC), since_leap_seconds_added=True) == 27
    assert TimeUtils.get_leap_seconds(datetime(2025, 1, 1, tzinfo=UTC), True) == 27


def test_get_leap_seconds_converts_input_to_utc() -> None:
    local = datetime(2025, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=5)))
    TimeUtils.get_leap_seconds(local)
    (seen,) = FakeLeapSecondData.seen_offset_inputs
    assert seen.utcoffset() == timedelta(0)
    assert seen == local


# --- to_tai / from_tai ---------------------------------------------------------------


def test_to_tai_adds_the_offset() -> None:
    utc = datetime(2024, 10, 27, 12, 0, 0, tzinfo=UTC)
    result = TimeUtils.to_tai(utc)
    assert result.replace(tzinfo=None) == datetime(2024, 10, 27, 12, 0, 37)
    assert result.tzinfo is tai


def test_to_tai_accepts_non_utc_input() -> None:
    plus_two = datetime(2024, 10, 27, 14, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    assert TimeUtils.to_tai(plus_two).replace(tzinfo=None) == datetime(2024, 10, 27, 12, 0, 37)


@pytest.mark.parametrize("second", [0, 1, 22, 23, 30, 59])
def test_from_tai_handles_every_second_value(second: int) -> None:
    """Regression: the old ``second + 37`` arithmetic raised ``ValueError`` for seconds >= 23."""
    value = datetime(2024, 1, 1, 0, 0, second, tzinfo=tai)
    result = TimeUtils.from_tai(value)
    assert result == datetime(2024, 1, 1, 0, 0, second, tzinfo=UTC) - FakeLeapSecondData.OFFSET


def test_from_tai_relabels_other_timezones_as_tai() -> None:
    TimeUtils.from_tai(datetime(2024, 1, 1, 0, 0, 5, tzinfo=timezone(timedelta(hours=3))))
    TimeUtils.from_tai(datetime(2024, 1, 1, 0, 0, 5))  # naive
    assert len(FakeLeapSecondData.seen_tai_inputs) == 2
    for received in FakeLeapSecondData.seen_tai_inputs:
        assert received.tzinfo is tai
        assert received.replace(tzinfo=None) == datetime(2024, 1, 1, 0, 0, 5)


def test_from_tai_keeps_sub_second_precision() -> None:
    TimeUtils.from_tai(datetime(2024, 1, 1, 0, 0, 5, 123456, tzinfo=tai))
    assert FakeLeapSecondData.seen_tai_inputs[-1].microsecond == 123456


def test_to_tai_then_from_tai_round_trips() -> None:
    utc = datetime(2024, 10, 27, 12, 0, 0, tzinfo=UTC)
    assert TimeUtils.from_tai(TimeUtils.to_tai(utc)) == utc


# --- parse_datetime -------------------------------------------------------------------


@pytest.mark.parametrize("empty", [None, ""])
def test_parse_datetime_empty_values(empty) -> None:
    assert TimeUtils.parse_datetime(empty) is None


def test_parse_datetime_z_suffix_gives_naive_datetime() -> None:
    parsed = TimeUtils.parse_datetime("2024-10-27T12:00:00Z")
    assert parsed == datetime(2024, 10, 27, 12, 0, 0)
    assert parsed.tzinfo is None


def test_parse_datetime_drops_microseconds() -> None:
    assert TimeUtils.parse_datetime("2024-10-27T12:00:00.987654") == datetime(2024, 10, 27, 12, 0, 0)


def test_parse_datetime_strips_whitespace() -> None:
    assert TimeUtils.parse_datetime("  2024-10-27T12:00:00Z  ") == datetime(2024, 10, 27, 12, 0, 0)


def test_parse_datetime_drops_the_offset_without_converting() -> None:
    assert TimeUtils.parse_datetime("2024-10-27T12:00:00+05:00") == datetime(2024, 10, 27, 12, 0, 0)


def test_parse_datetime_date_only() -> None:
    assert TimeUtils.parse_datetime("2024-10-27") == datetime(2024, 10, 27)


def test_parse_datetime_roundtrips_str_of_now() -> None:
    now = TimeUtils.now()
    assert TimeUtils.parse_datetime(str(now)) == now.replace(tzinfo=None, microsecond=0)


def test_parse_datetime_invalid_text_raises() -> None:
    with pytest.raises(ValueError):
        TimeUtils.parse_datetime("not a date")


# --- placeholder classes and demo --------------------------------------------------------


def test_placeholder_classes_are_instantiable_and_exported() -> None:
    assert isinstance(DateUtils(), DateUtils)
    assert isinstance(DateTimeUtils(), DateTimeUtils)
    assert set(datetime_package.__all__) == {"DateTimeUtils", "DateUtils", "TimeUtils"}
    for name in datetime_package.__all__:
        assert hasattr(datetime_package, name)


def test_demo_prints_a_report(capsys) -> None:
    time_module.main()
    out = capsys.readouterr().out
    assert "The AI-UTC offset on" in out
    assert "37" in out
    assert "UTC:" in out


def test_importing_the_module_has_no_side_effects(capsys) -> None:
    importlib.reload(time_module)
    assert capsys.readouterr().out == ""


# --- real library (skipped when the leap-second list cannot be loaded) -------------------


@pytest.fixture
def real_leap_seconds(monkeypatch):
    try:
        LeapSecondData.from_standard_source()
    except Exception as exc:  # no local list and no network
        pytest.skip(f"leap-second data unavailable: {exc}")
    monkeypatch.setattr(time_module, "LeapSecondData", LeapSecondData)


def test_real_data_offsets(real_leap_seconds) -> None:
    assert TimeUtils.get_leap_seconds(datetime(2016, 1, 1, tzinfo=UTC)) == 36
    assert TimeUtils.get_leap_seconds(datetime(2025, 1, 1, tzinfo=UTC)) == 37
    assert TimeUtils.get_leap_seconds(datetime(2025, 1, 1, tzinfo=UTC), True) == 27


def test_real_data_round_trip(real_leap_seconds) -> None:
    utc = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    value = TimeUtils.to_tai(utc)
    assert value.replace(tzinfo=None) - utc.replace(tzinfo=None) == timedelta(seconds=37)
    assert TimeUtils.from_tai(value) == utc


@pytest.mark.parametrize("second", [0, 22, 23, 59])
def test_real_data_from_tai_for_any_second(real_leap_seconds, second: int) -> None:
    value = datetime(2025, 1, 1, 12, 30, second, tzinfo=tai)
    assert TimeUtils.from_tai(value) == datetime(2025, 1, 1, 12, 30, second, tzinfo=UTC) - timedelta(seconds=37)
