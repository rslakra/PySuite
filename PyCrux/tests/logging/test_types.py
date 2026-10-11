"""Tests for ``pycrux.logging.types`` — ``LogLevel``, ``LogFormat``, ``LogTarget``."""

import logging

import pytest

from pycrux.logging import LogFormat, LogLevel, LogTarget

# --- LogLevel ------------------------------------------------------------------


def test_log_level_matches_stdlib_numbers() -> None:
    assert LogLevel.CRITICAL == logging.CRITICAL
    assert LogLevel.ERROR == logging.ERROR
    assert LogLevel.WARN == logging.WARNING
    assert LogLevel.INFO == logging.INFO
    assert LogLevel.DEBUG == logging.DEBUG
    assert LogLevel.NOTSET == logging.NOTSET


def test_log_level_names_and_helpers() -> None:
    assert LogLevel.names() == ["CRITICAL", "ERROR", "WARN", "INFO", "DEBUG", "NOTSET"]
    assert LogLevel.INFO.equals("info")
    assert LogLevel.INFO.not_equals("debug")
    assert LogLevel.INFO.equals_any(["debug", "INFO"])


@pytest.mark.parametrize(
    ("text", "expected"),
    [("warn", LogLevel.WARN), ("ERROR", LogLevel.ERROR), ("  Debug ", LogLevel.DEBUG), ("notset", LogLevel.NOTSET)],
)
def test_log_level_from_string(text: str, expected: LogLevel) -> None:
    assert LogLevel.from_string(text) is expected


def test_log_level_from_string_returns_member_unchanged() -> None:
    assert LogLevel.from_string(LogLevel.INFO) is LogLevel.INFO


@pytest.mark.parametrize("bad", [None, "", "   ", 20, "warning", "loud"])
def test_log_level_from_string_rejects_invalid(bad) -> None:
    with pytest.raises(ValueError, match="Invalid LogLevel"):
        LogLevel.from_string(bad)


def test_log_level_error_lists_valid_values() -> None:
    with pytest.raises(ValueError, match="CRITICAL, ERROR, WARN, INFO, DEBUG, NOTSET"):
        LogLevel.from_string("loud")


# --- LogFormat -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("text", LogFormat.TEXT),
        ("JSON", LogFormat.JSON),
        (" xml ", LogFormat.XML),
        (".json", LogFormat.JSON),
        (".XML", LogFormat.XML),
        ("txt", LogFormat.TEXT),
        ("log", LogFormat.TEXT),
        ("jsonl", LogFormat.JSON),
        ("ndjson", LogFormat.JSON),
        (".txt", LogFormat.TEXT),
    ],
)
def test_log_format_from_string(text: str, expected: LogFormat) -> None:
    assert LogFormat.from_string(text) is expected


def test_log_format_from_string_returns_member_unchanged() -> None:
    assert LogFormat.from_string(LogFormat.XML) is LogFormat.XML


@pytest.mark.parametrize("bad", [None, "", "yaml", ".csv"])
def test_log_format_from_string_rejects_invalid(bad) -> None:
    with pytest.raises(ValueError):
        LogFormat.from_string(bad)


def test_log_format_extension() -> None:
    assert LogFormat.TEXT.extension == ".txt"
    assert LogFormat.JSON.extension == ".json"
    assert LogFormat.XML.extension == ".xml"


# --- LogTarget -----------------------------------------------------------------


def test_log_target() -> None:
    assert LogTarget.from_string("Console") is LogTarget.CONSOLE
    assert LogTarget.from_string("FILE") is LogTarget.FILE
    assert LogTarget.names() == ["CONSOLE", "FILE"]
    with pytest.raises(ValueError):
        LogTarget.from_string("socket")
