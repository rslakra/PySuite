from pathlib import Path

from core.converter.abstract import AbstractConverter


class Word2PdfConverter(AbstractConverter):
    """Convert Word documents to PDF files."""

    source_extensions = frozenset({"docx"})
    dest_extensions = frozenset({"pdf"})

    def convert(self, source: Path, destination: Path) -> None:
        try:
            from docx2pdf import convert
        except ImportError as exc:
            raise ImportError(
                "Missing required library. Install with: pip install docx2pdf"
            ) from exc

        source = Path(source)
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        convert(str(source), str(destination))
