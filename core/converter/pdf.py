from pathlib import Path

from core.converter.abstract import AbstractConverter


class Pdf2WordConverter(AbstractConverter):
    """Convert PDF files to Word documents."""

    source_extensions = frozenset({"pdf"})
    dest_extensions = frozenset({"docx"})

    def convert(self, source: Path, destination: Path) -> None:
        try:
            from pdf2docx import Converter
        except ImportError as exc:
            raise ImportError(
                "Missing required library. Install with: pip install pdf2docx"
            ) from exc

        source = Path(source)
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        converter = Converter(str(source))
        try:
            converter.convert(str(destination))
        finally:
            converter.close()
