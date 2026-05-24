from pathlib import Path

from core.converter.abstract import AbstractConverter


class Markdown2WordConverter(AbstractConverter):
    """Convert markdown files to Word documents."""

    source_extensions = frozenset({"md", "markdown"})
    dest_extensions = frozenset({"docx"})

    def convert(self, source: Path, destination: Path) -> None:
        try:
            import markdown
            from docx import Document
        except ImportError as exc:
            raise ImportError(
                "Missing required libraries. Install with: pip install python-docx markdown"
            ) from exc

        source = Path(source)
        destination = Path(destination)

        md_content = source.read_text(encoding="utf-8")
        doc = Document()

        # Convert markdown to HTML first (for better parsing)
        markdown.markdown(md_content, extensions=["extra", "codehilite", "tables"])

        lines = md_content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("# "):
                doc.add_heading(line[2:].strip(), level=1)
            elif line.startswith("## "):
                doc.add_heading(line[3:].strip(), level=2)
            elif line.startswith("### "):
                doc.add_heading(line[4:].strip(), level=3)
            elif line.startswith("#### "):
                doc.add_heading(line[5:].strip(), level=4)
            elif line.startswith("##### "):
                doc.add_heading(line[6:].strip(), level=5)
            elif line.startswith("###### "):
                doc.add_heading(line[7:].strip(), level=6)
            elif line.startswith("```"):
                i += 1
                continue
            elif line.startswith("- ") or line.startswith("* "):
                doc.add_paragraph(line[2:].strip(), style="List Bullet")
            elif line and line[0].isdigit() and ". " in line[:5]:
                doc.add_paragraph(line.split(". ", 1)[1].strip(), style="List Number")
            elif line:
                doc.add_paragraph(line)
            else:
                doc.add_paragraph()

            i += 1

        destination.parent.mkdir(parents=True, exist_ok=True)
        doc.save(destination)


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
