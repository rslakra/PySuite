from pathlib import Path

from core.converter.abstract import AbstractConverter
from core.converter.markdown import Word2MarkdownConverter
from core.converter.pdf import Word2PdfConverter
from office.word.converter import Markdown2WordConverter, Pdf2WordConverter

_CONVERTERS: tuple[type[AbstractConverter], ...] = (
    Markdown2WordConverter,
    Word2MarkdownConverter,
    Word2PdfConverter,
    Pdf2WordConverter,
)

_EXTENSION_ALIASES = {
    "markdown": "md",
}


def normalize_extension(path: Path | str) -> str:
    ext = Path(path).suffix.lower().lstrip(".")
    return _EXTENSION_ALIASES.get(ext, ext)


def list_conversions() -> list[tuple[str, str]]:
    conversions: set[tuple[str, str]] = set()
    for converter_cls in _CONVERTERS:
        for source_ext in converter_cls.source_extensions:
            for dest_ext in converter_cls.dest_extensions:
                # Collapse aliases (e.g. markdown -> md) for display
                src = normalize_extension(f"file.{source_ext}")
                dst = normalize_extension(f"file.{dest_ext}")
                conversions.add((src, dst))
    return sorted(conversions)


def dest_extensions_for_source(source: Path | str) -> list[str]:
    source_ext = normalize_extension(source)
    return sorted(
        {
            dest_ext
            for src_ext, dest_ext in list_conversions()
            if src_ext == source_ext
        }
    )


def default_dest_extension(source: Path | str) -> str:
    options = dest_extensions_for_source(source)
    if not options:
        source_ext = normalize_extension(source)
        raise ValueError(f"No supported conversions for .{source_ext} files.")

    if len(options) == 1:
        return options[0]

    preferred = {"docx": "md"}
    source_ext = normalize_extension(source)
    return preferred.get(source_ext, options[0])


def default_destination_path(source: Path | str, dest_format: str | None = None) -> Path:
    source = Path(source)
    dest_ext = dest_format or default_dest_extension(source)
    normalized = normalize_extension(f"file.{dest_ext}")
    return source.with_suffix(f".{normalized}")


def get_converter(source: Path | str, destination: Path | str) -> AbstractConverter:
    source_ext = normalize_extension(source)
    dest_ext = normalize_extension(destination)

    for converter_cls in _CONVERTERS:
        if source_ext in converter_cls.source_extensions and dest_ext in converter_cls.dest_extensions:
            return converter_cls()

    supported = ", ".join(f"{src} -> {dst}" for src, dst in list_conversions())
    raise ValueError(
        f"Unsupported conversion: {source_ext} -> {dest_ext}. "
        f"Supported conversions: {supported}"
    )
