"""Tests for ``pycrux.converter.registry``."""

from pathlib import Path

import pytest

from pycrux.converter.markdown import Word2MarkdownConverter
from pycrux.converter.pdf import Word2PdfConverter
from pycrux.converter.registry import (
    default_dest_extension,
    default_destination_path,
    dest_extensions_for_source,
    get_converter,
    list_conversions,
    normalize_extension,
)
from pycrux.office.word.converter import Markdown2WordConverter, Pdf2WordConverter

# --- normalize_extension -----------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("a.md", "md"),
        ("a.MD", "md"),
        ("a.markdown", "md"),
        ("a.MARKDOWN", "md"),
        ("report.PDF", "pdf"),
        ("notes.docx", "docx"),
        ("archive.tar.gz", "gz"),
        ("/some/dir.v2/file.docx", "docx"),
        ("noextension", ""),
        (".hidden", ""),
        (Path("x/y.docx"), "docx"),
    ],
)
def test_normalize_extension(value, expected: str) -> None:
    assert normalize_extension(value) == expected


# --- list_conversions --------------------------------------------------------------


def test_list_conversions_is_sorted_and_collapses_aliases() -> None:
    assert list_conversions() == [
        ("docx", "md"),
        ("docx", "pdf"),
        ("md", "docx"),
        ("pdf", "docx"),
    ]


# --- dest_extensions_for_source ---------------------------------------------------


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("a.docx", ["md", "pdf"]),
        ("a.md", ["docx"]),
        ("a.markdown", ["docx"]),
        ("a.pdf", ["docx"]),
        (Path("a.DOCX"), ["md", "pdf"]),
        ("a.txt", []),
        ("noext", []),
    ],
)
def test_dest_extensions_for_source(source, expected: list[str]) -> None:
    assert dest_extensions_for_source(source) == expected


# --- default_dest_extension --------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "expected"),
    [("a.docx", "md"), ("a.md", "docx"), ("a.markdown", "docx"), ("a.pdf", "docx")],
)
def test_default_dest_extension(source: str, expected: str) -> None:
    assert default_dest_extension(source) == expected


def test_default_dest_extension_unsupported_source() -> None:
    with pytest.raises(ValueError, match=r"No supported conversions for \.txt files\."):
        default_dest_extension("a.txt")


# --- default_destination_path ------------------------------------------------------


def test_default_destination_path_uses_default_format() -> None:
    assert default_destination_path("/x/a.docx") == Path("/x/a.md")
    assert default_destination_path(Path("/x/a.md")) == Path("/x/a.docx")
    assert default_destination_path("a.pdf") == Path("a.docx")


def test_default_destination_path_with_explicit_format() -> None:
    assert default_destination_path("/x/a.docx", "pdf") == Path("/x/a.pdf")
    assert default_destination_path("/x/a.docx", "markdown") == Path("/x/a.md")
    assert default_destination_path("/x/a.docx", ".PDF") == Path("/x/a.pdf")


def test_default_destination_path_propagates_unsupported_source() -> None:
    with pytest.raises(ValueError):
        default_destination_path("a.txt")


def test_default_destination_path_only_replaces_the_last_suffix() -> None:
    assert default_destination_path("/x/my.notes.docx") == Path("/x/my.notes.md")


# --- get_converter -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "destination", "cls"),
    [
        ("a.md", "b.docx", Markdown2WordConverter),
        ("a.markdown", "b.docx", Markdown2WordConverter),
        ("a.docx", "b.md", Word2MarkdownConverter),
        ("a.docx", "b.markdown", Word2MarkdownConverter),
        ("a.docx", "b.pdf", Word2PdfConverter),
        ("a.pdf", "b.docx", Pdf2WordConverter),
        (Path("a.MD"), Path("b.DOCX"), Markdown2WordConverter),
    ],
)
def test_get_converter_returns_matching_instance(source, destination, cls) -> None:
    assert type(get_converter(source, destination)) is cls


def test_get_converter_creates_a_new_instance_each_time() -> None:
    assert get_converter("a.md", "b.docx") is not get_converter("a.md", "b.docx")


@pytest.mark.parametrize(
    ("source", "destination"),
    [("a.md", "b.pdf"), ("a.pdf", "b.md"), ("a.txt", "b.docx"), ("a.docx", "b.docx"), ("a", "b")],
)
def test_get_converter_rejects_unsupported_pairs(source: str, destination: str) -> None:
    with pytest.raises(ValueError, match="Unsupported conversion") as info:
        get_converter(source, destination)
    message = str(info.value)
    assert "Supported conversions:" in message
    assert "docx -> md" in message and "pdf -> docx" in message
