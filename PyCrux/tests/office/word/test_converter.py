"""Tests for ``pycrux.office.word.converter`` — Markdown→Word and PDF→Word converters."""

import pytest
from docx import Document

import pycrux.office.word.converter as word_module
from pycrux.converter import AbstractConverter
from pycrux.office.word.converter import Markdown2WordConverter, Pdf2WordConverter


def _read(path) -> list[tuple[str, str]]:
    return [(p.style.name, p.text) for p in Document(path).paragraphs]


# --- Markdown2WordConverter ---------------------------------------------------------


def test_markdown_converter_contract() -> None:
    assert issubclass(Markdown2WordConverter, AbstractConverter)
    assert Markdown2WordConverter.source_extensions == {"md", "markdown"}
    assert Markdown2WordConverter.dest_extensions == {"docx"}


def test_markdown_to_word_maps_every_block_type(tmp_path) -> None:
    source, destination = tmp_path / "in.md", tmp_path / "out.docx"
    source.write_text(
        "\n".join(
            [
                "# H1",
                "## H2",
                "### H3",
                "#### H4",
                "##### H5",
                "###### H6",
                "- dash bullet",
                "* star bullet",
                "1. first",
                "10. tenth",
                "plain text",
                "",
                "```python",
                "code line",
                "```",
                "####### seven hashes",
            ]
        ),
        encoding="utf-8",
    )

    Markdown2WordConverter().convert(source, destination)

    assert _read(destination) == [
        ("Heading 1", "H1"),
        ("Heading 2", "H2"),
        ("Heading 3", "H3"),
        ("Heading 4", "H4"),
        ("Heading 5", "H5"),
        ("Heading 6", "H6"),
        ("List Bullet", "dash bullet"),
        ("List Bullet", "star bullet"),
        ("List Number", "first"),
        ("List Number", "tenth"),
        ("Normal", "plain text"),
        ("Normal", ""),  # blank line
        # the two ``` fence lines are skipped; the code line is kept as a paragraph
        ("Normal", "code line"),
        ("Normal", "####### seven hashes"),
    ]


def test_markdown_to_word_strips_indentation(tmp_path) -> None:
    source, destination = tmp_path / "in.md", tmp_path / "out.docx"
    source.write_text("   # Indented heading   \n   - indented bullet", encoding="utf-8")
    Markdown2WordConverter().convert(source, destination)
    assert _read(destination) == [("Heading 1", "Indented heading"), ("List Bullet", "indented bullet")]


def test_markdown_to_word_empty_file(tmp_path) -> None:
    source, destination = tmp_path / "in.md", tmp_path / "out.docx"
    source.write_text("", encoding="utf-8")
    Markdown2WordConverter().convert(source, destination)
    assert _read(destination) == [("Normal", "")]


def test_markdown_to_word_creates_directories_and_accepts_strings(tmp_path) -> None:
    source = tmp_path / "in.md"
    source.write_text("# T", encoding="utf-8")
    destination = tmp_path / "x" / "y" / "out.docx"
    Markdown2WordConverter().convert(str(source), str(destination))  # type: ignore[arg-type]
    assert _read(destination) == [("Heading 1", "T")]


def test_markdown_to_word_preserves_unicode(tmp_path) -> None:
    source, destination = tmp_path / "in.md", tmp_path / "out.docx"
    source.write_text("# héllo ✓", encoding="utf-8")
    Markdown2WordConverter().convert(source, destination)
    assert _read(destination) == [("Heading 1", "héllo ✓")]


def test_markdown_to_word_missing_source_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        Markdown2WordConverter().convert(tmp_path / "missing.md", tmp_path / "out.docx")


@pytest.mark.parametrize("missing", ["markdown", "Document"])
def test_markdown_to_word_reports_missing_libraries(monkeypatch, tmp_path, missing: str) -> None:
    monkeypatch.setattr(word_module, missing, None)
    with pytest.raises(ImportError, match="pip install python-docx markdown"):
        Markdown2WordConverter().convert(tmp_path / "in.md", tmp_path / "out.docx")


# --- Pdf2WordConverter -----------------------------------------------------------------


class FakeConverter:
    """Records the calls made by ``Pdf2WordConverter``."""

    instances: list["FakeConverter"] = []
    fail = False

    def __init__(self, pdf_path: str) -> None:
        self.pdf_path = pdf_path
        self.converted_to: str | None = None
        self.closed = False
        FakeConverter.instances.append(self)

    def convert(self, docx_path: str) -> None:
        if FakeConverter.fail:
            raise RuntimeError("corrupt pdf")
        self.converted_to = docx_path

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_pdf2docx(monkeypatch):
    FakeConverter.instances = []
    FakeConverter.fail = False
    monkeypatch.setattr(word_module, "Converter", FakeConverter)
    return FakeConverter


def test_pdf_converter_contract() -> None:
    assert issubclass(Pdf2WordConverter, AbstractConverter)
    assert Pdf2WordConverter.source_extensions == {"pdf"}
    assert Pdf2WordConverter.dest_extensions == {"docx"}


def test_pdf_to_word_uses_pdf2docx_and_closes(fake_pdf2docx, tmp_path) -> None:
    source, destination = tmp_path / "in.pdf", tmp_path / "out.docx"
    Pdf2WordConverter().convert(source, destination)

    (instance,) = fake_pdf2docx.instances
    assert instance.pdf_path == str(source)
    assert instance.converted_to == str(destination)
    assert instance.closed is True


def test_pdf_to_word_creates_destination_directories(fake_pdf2docx, tmp_path) -> None:
    destination = tmp_path / "deep" / "out.docx"
    Pdf2WordConverter().convert(tmp_path / "in.pdf", destination)
    assert destination.parent.is_dir()


def test_pdf_to_word_closes_even_when_conversion_fails(fake_pdf2docx, tmp_path) -> None:
    fake_pdf2docx.fail = True
    with pytest.raises(RuntimeError, match="corrupt pdf"):
        Pdf2WordConverter().convert(tmp_path / "in.pdf", tmp_path / "out.docx")
    assert fake_pdf2docx.instances[0].closed is True


def test_pdf_to_word_reports_missing_library(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(word_module, "Converter", None)
    with pytest.raises(ImportError, match="pip install pdf2docx"):
        Pdf2WordConverter().convert(tmp_path / "in.pdf", tmp_path / "out.docx")


def test_module_imports_without_markdown_and_docx(reload_without, tmp_path) -> None:
    module = reload_without(word_module, "docx")
    assert module.Document is None and module.markdown is None
    with pytest.raises(ImportError, match="pip install python-docx markdown"):
        module.Markdown2WordConverter().convert(tmp_path / "in.md", tmp_path / "out.docx")


def test_module_imports_without_pdf2docx(reload_without, tmp_path) -> None:
    module = reload_without(word_module, "pdf2docx")
    assert module.Converter is None
    with pytest.raises(ImportError, match="pip install pdf2docx"):
        module.Pdf2WordConverter().convert(tmp_path / "in.pdf", tmp_path / "out.docx")


def test_pdf_to_word_with_a_real_pdf(tmp_path) -> None:
    pymupdf = pytest.importorskip("pymupdf")
    source, destination = tmp_path / "in.pdf", tmp_path / "out.docx"
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Hello from a real PDF")
    pdf.save(str(source))
    pdf.close()

    Pdf2WordConverter().convert(source, destination)

    text = "\n".join(text for _, text in _read(destination))
    assert "Hello from a real PDF" in text
