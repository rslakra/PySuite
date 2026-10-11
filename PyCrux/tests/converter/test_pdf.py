"""Tests for ``pycrux.converter.pdf.Word2PdfConverter``.

``docx2pdf`` drives Microsoft Word, so the conversion function is replaced with a recorder.
"""

import pytest

import pycrux.converter.pdf as pdf_module
from pycrux.converter import AbstractConverter
from pycrux.converter.pdf import Word2PdfConverter


def test_class_contract() -> None:
    assert issubclass(Word2PdfConverter, AbstractConverter)
    assert Word2PdfConverter.source_extensions == {"docx"}
    assert Word2PdfConverter.dest_extensions == {"pdf"}


def test_delegates_to_docx2pdf_with_string_paths(monkeypatch, tmp_path) -> None:
    calls: list[tuple] = []
    monkeypatch.setattr(pdf_module, "docx2pdf_convert", lambda *args: calls.append(args))

    source, destination = tmp_path / "in.docx", tmp_path / "out.pdf"
    Word2PdfConverter().convert(source, destination)

    assert calls == [(str(source), str(destination))]


def test_creates_missing_destination_directories(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(pdf_module, "docx2pdf_convert", lambda *args: None)
    destination = tmp_path / "a" / "b" / "out.pdf"
    Word2PdfConverter().convert(tmp_path / "in.docx", destination)
    assert destination.parent.is_dir()


def test_accepts_string_paths(monkeypatch, tmp_path) -> None:
    calls: list[tuple] = []
    monkeypatch.setattr(pdf_module, "docx2pdf_convert", lambda *args: calls.append(args))
    Word2PdfConverter().convert(str(tmp_path / "in.docx"), str(tmp_path / "out.pdf"))  # type: ignore[arg-type]
    assert calls == [(str(tmp_path / "in.docx"), str(tmp_path / "out.pdf"))]


def test_conversion_errors_propagate(monkeypatch, tmp_path) -> None:
    def boom(*_args) -> None:
        raise RuntimeError("Word is not installed")

    monkeypatch.setattr(pdf_module, "docx2pdf_convert", boom)
    with pytest.raises(RuntimeError, match="Word is not installed"):
        Word2PdfConverter().convert(tmp_path / "in.docx", tmp_path / "out.pdf")


def test_reports_a_missing_docx2pdf_library(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(pdf_module, "docx2pdf_convert", None)
    with pytest.raises(ImportError, match="pip install docx2pdf"):
        Word2PdfConverter().convert(tmp_path / "in.docx", tmp_path / "out.pdf")
    assert not (tmp_path / "out.pdf").exists()


def test_module_imports_without_docx2pdf(reload_without, tmp_path) -> None:
    module = reload_without(pdf_module, "docx2pdf")
    assert module.docx2pdf_convert is None
    with pytest.raises(ImportError, match="pip install docx2pdf"):
        module.Word2PdfConverter().convert(tmp_path / "in.docx", tmp_path / "out.pdf")
