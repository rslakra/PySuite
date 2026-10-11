"""Tests for ``pycrux.office.excel.base`` — ``ExcelUtils`` and ``ExcelDataType``."""

import pytest

import pycrux.office.excel as excel_package
from pycrux.office.excel import ExcelDataType, ExcelUtils

# --- ExcelUtils.sanitize_filename ---------------------------------------------------


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("plain", "plain"),
        ("  padded  ", "padded"),
        ("Sheet 1", "Sheet 1"),
        ("a/b", "a_b"),
        ("a\\b", "a_b"),
        ('a<b>c:d"e|f?g*h', "a_b_c_d_e_f_g_h"),
        ("tab\there", "tab_here"),
        ("nul\x00char", "nul_char"),
        ("many    spaces   inside", "many spaces inside"),
        ("line\nbreak", "line_break"),
        ("héllo ✓", "héllo ✓"),
        ("2-26 update dim_agent", "2-26 update dim_agent"),
    ],
)
def test_sanitize_filename(label: str, expected: str) -> None:
    assert ExcelUtils.sanitize_filename(label) == expected


@pytest.mark.parametrize("empty", ["", "   ", "\t\n"])
def test_sanitize_filename_falls_back_to_sheet(empty: str) -> None:
    assert ExcelUtils.sanitize_filename(empty) == "sheet"


def test_sanitize_filename_result_is_a_safe_stem() -> None:
    cleaned = ExcelUtils.sanitize_filename('..\\/:*?"<>| weird')
    assert not any(ch in cleaned for ch in '<>:"/\\|?*')


def test_sanitize_filename_is_idempotent() -> None:
    once = ExcelUtils.sanitize_filename("a/b   c?")
    assert ExcelUtils.sanitize_filename(once) == once


# --- ExcelDataType -----------------------------------------------------------------


def test_data_type_members_and_values() -> None:
    assert [m.name for m in ExcelDataType] == [
        "INTEGER",
        "LONG",
        "FLOAT",
        "SINGLE",
        "DOUBLE",
        "STRING",
        "VARCHAR",
        "BOOLEAN",
        "VARIANT",
        "DATE",
        "TIMESTAMP",
        "JSON",
    ]
    assert all(m.value == m.name for m in ExcelDataType)


def test_data_type_behaves_like_its_cell_text() -> None:
    assert ExcelDataType.INTEGER == "INTEGER"
    assert isinstance(ExcelDataType.STRING, str)
    assert ExcelDataType("DATE") is ExcelDataType.DATE
    with pytest.raises(ValueError):
        ExcelDataType("integer")  # values are case-sensitive cell tokens


def test_hint_tokens_contains_every_value() -> None:
    tokens = ExcelDataType.HINT_TOKENS
    assert isinstance(tokens, frozenset)
    assert tokens == {m.value for m in ExcelDataType}
    assert "FLOAT" in tokens and "float" not in tokens


def test_package_exports() -> None:
    assert set(excel_package.__all__) == {"ExcelDataType", "ExcelUtils"}
