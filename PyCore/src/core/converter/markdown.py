from pathlib import Path

from core.converter.abstract import AbstractConverter


class Word2MarkdownConverter(AbstractConverter):
    """Convert Word documents to markdown files."""

    source_extensions = frozenset({"docx"})
    dest_extensions = frozenset({"md", "markdown"})

    def convert(self, source: Path, destination: Path) -> None:
        try:
            from docx import Document
        except ImportError as exc:
            raise ImportError(
                "Missing required library. Install with: pip install python-docx"
            ) from exc

        source = Path(source)
        destination = Path(destination)

        doc = Document(source)
        lines: list[str] = []

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                lines.append("")
                continue

            style_name = paragraph.style.name if paragraph.style else ""
            if style_name.startswith("Heading"):
                level_text = style_name.replace("Heading ", "").strip()
                level = int(level_text) if level_text.isdigit() else 1
                lines.append(f"{'#' * level} {text}")
            elif "List Bullet" in style_name:
                lines.append(f"- {text}")
            elif "List Number" in style_name:
                lines.append(f"1. {text}")
            else:
                lines.append(text)

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("\n".join(lines), encoding="utf-8")

