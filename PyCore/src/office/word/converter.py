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
