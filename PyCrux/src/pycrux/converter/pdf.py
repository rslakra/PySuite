from pathlib import Path

from pycrux.converter.abstract import AbstractConverter

try:
    from docx2pdf import convert as docx2pdf_convert
except ImportError:  # optional dependency: pip install "Amey-PyCrux[convert]"
    docx2pdf_convert = None  # type: ignore[assignment]


class Word2PdfConverter(AbstractConverter):
    """Convert Word documents to PDF files."""

    source_extensions = frozenset({"docx"})
    dest_extensions = frozenset({"pdf"})

    def convert(self, source: Path, destination: Path) -> None:
        if docx2pdf_convert is None:
            raise ImportError(
                "Missing required library. Install with: pip install docx2pdf"
            )

        source = Path(source)
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        docx2pdf_convert(str(source), str(destination))
