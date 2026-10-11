#!/usr/bin/env python3
"""Command-line interface for PyCrux document conversion."""

import argparse
import sys
from pathlib import Path

from pycrux.converter.registry import (
    default_destination_path,
    get_converter,
    list_conversions,
    normalize_extension,
)


def _normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    if argv[0] == "convert":
        return argv[1:]
    if argv[0] == "list":
        return ["--list"]
    return argv


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pycrux.cli",
        description="Convert documents between formats (markdown, Word, PDF).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m pycrux.cli -i README.md\n"
            "  python -m pycrux.cli -i README.md docx\n"
            "  python -m pycrux.cli -i notes.docx pdf\n"
            "  python -m pycrux.cli -i notes.docx -f pdf\n"
            "  python -m pycrux.cli -i report.pdf --out /tmp/report.docx\n"
            "  python -m pycrux.cli README.md README.docx\n"
            "  python -m pycrux.cli --list"
        ),
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        dest="input_path",
        metavar="PATH",
        help="Path to the input file",
    )
    parser.add_argument(
        "--out",
        type=Path,
        dest="output_path",
        metavar="PATH",
        help="Output file path (optional)",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="dest_format",
        metavar="FORMAT",
        help="Output format: md, markdown, docx, or pdf. "
        "Optional when FORMAT is given as a trailing argument.",
    )
    parser.add_argument(
        "--output",
        dest="dest_format",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--to",
        dest="dest_format",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List supported format conversions",
    )
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        metavar="INPUT",
        help="Input file path (alternative to --input)",
    )
    parser.add_argument(
        "destination",
        nargs="?",
        type=Path,
        metavar="FORMAT_OR_PATH",
        help="Output format or file path (trailing argument; see also --format / --out)",
    )
    return parser


def _default_destination(source: Path, dest_format: str | None = None) -> Path:
    return default_destination_path(source, dest_format)


def _format_name(value: Path | str) -> str | None:
    """Return normalized dest extension when value is a format name (pdf, md, …)."""
    text = str(value).strip()
    if not text or "/" in text or "\\" in text:
        return None

    token = (
        normalize_extension(text)
        if Path(text).suffix
        else normalize_extension(f"file.{text}")
    )
    dest_exts = {dst for _, dst in list_conversions()}
    return token if token in dest_exts else None


def _coerce_trailing_format(args: argparse.Namespace) -> None:
    """Treat a trailing format token (pdf, md, …) as the target format."""
    if args.dest_format:
        return

    if args.input_path and args.source and args.destination is None:
        dest_format = _format_name(args.source)
        if dest_format is not None:
            args.dest_format = dest_format
            args.source = None
            return

    if args.source and args.destination and args.output_path is None:
        dest_format = _format_name(args.destination)
        if dest_format is not None:
            args.dest_format = dest_format
            args.destination = None


def _resolve_paths(args: argparse.Namespace) -> tuple[Path | None, Path | None]:
    source = args.input_path or args.source
    destination = args.output_path or args.destination
    return source, destination


def _run_convert(args: argparse.Namespace) -> int:
    _coerce_trailing_format(args)
    source, destination = _resolve_paths(args)

    if source is None:
        print(
            "Error: input file is required. Use --input PATH or provide INPUT as a positional argument.",
            file=sys.stderr,
        )
        return 1

    source = source.resolve()

    if not source.is_file():
        print(f"Error: input file not found: {source}", file=sys.stderr)
        return 1

    if destination is not None:
        destination = destination.resolve()
    else:
        try:
            destination = _default_destination(source, args.dest_format).resolve()
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    if source == destination:
        print("Error: input and output must be different files.", file=sys.stderr)
        return 1

    try:
        converter = get_converter(source, destination)
        converter.convert(source, destination)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ImportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: conversion failed: {exc}", file=sys.stderr)
        return 1

    print(f"Converted {source} -> {destination}")
    return 0


def _run_list() -> int:
    print("Supported conversions:")
    for source_ext, dest_ext in list_conversions():
        print(f"  {source_ext} -> {dest_ext}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = _normalize_argv(list(argv if argv is not None else sys.argv[1:]))

    if not argv:
        _build_parser().print_help()
        return 0

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.list:
        return _run_list()

    source, destination = _resolve_paths(args)
    if source is not None or destination is not None or args.dest_format:
        return _run_convert(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
