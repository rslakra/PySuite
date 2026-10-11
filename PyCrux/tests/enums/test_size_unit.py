"""Tests for ``pycrux.enums.size_unit.SizeUnit``."""

import pytest

from pycrux.enums import SizeUnit


def test_members_are_binary_multipliers() -> None:
    assert SizeUnit.B == 1
    assert SizeUnit.KB == 1024
    assert SizeUnit.MB == 1024**2
    assert SizeUnit.GB == 1024**3
    assert SizeUnit.TB == 1024**4


def test_names() -> None:
    assert SizeUnit.names() == ["B", "KB", "MB", "GB", "TB"]


# --- from_string ---------------------------------------------------------------


def test_from_string() -> None:
    assert SizeUnit.from_string("mb") is SizeUnit.MB
    assert SizeUnit.from_string("KB") is SizeUnit.KB
    assert SizeUnit.from_string("  gb  ") is SizeUnit.GB
    assert SizeUnit.from_string(SizeUnit.TB) is SizeUnit.TB


@pytest.mark.parametrize("bad", [None, "", "   ", "pb", "kilobyte", 5])
def test_from_string_returns_none_for_unknown(bad) -> None:
    assert SizeUnit.from_string(bad) is None


# --- normalize_bytes / to_bytes ------------------------------------------------


def test_normalize_bytes_clamps_and_truncates() -> None:
    assert SizeUnit.normalize_bytes(10) == 10
    assert SizeUnit.normalize_bytes(-5) == 0
    assert SizeUnit.normalize_bytes(7.9) == 7
    assert SizeUnit.normalize_bytes(0) == 0


def test_to_bytes() -> None:
    assert SizeUnit.to_bytes(2048) == 2048
    assert SizeUnit.to_bytes(-1) == 0


# --- from_bytes and the to_* helpers ------------------------------------------


def test_from_bytes_on_members() -> None:
    assert SizeUnit.B.from_bytes(512) == 512.0
    assert SizeUnit.KB.from_bytes(2048) == 2.0
    assert SizeUnit.MB.from_bytes(1024**2 // 2) == 0.5
    assert SizeUnit.KB.from_bytes(-100) == 0.0


def test_to_kb_mb_gb_tb() -> None:
    assert SizeUnit.to_kb(2048) == 2.0
    assert SizeUnit.to_mb(3 * 1024**2) == 3.0
    assert SizeUnit.to_gb(1024**3) == 1.0
    assert SizeUnit.to_tb(2 * 1024**4) == 2.0


# --- format_bytes --------------------------------------------------------------


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (-1, "0 B"),
        (0, "0 B"),
        (1, "1 B"),
        (1023, "1023 B"),
        (1024, "1.00 KB"),
        (1536, "1.50 KB"),
        (1024**2 - 1, "1024.00 KB"),
        (1024**2, "1.00 MB"),
        (5 * 1024**2, "5.00 MB"),
        (1024**3, "1.00 GB"),
        (1024**4, "1.00 TB"),
        (5 * 1024**4, "5.00 TB"),
        (2048, "2.00 KB"),
    ],
)
def test_format_bytes(size: int, expected: str) -> None:
    assert SizeUnit.format_bytes(size) == expected
