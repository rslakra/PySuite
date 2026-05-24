#!/usr/bin/env python3
"""Command-line interface for PySuite document conversion."""

import argparse
import sys
from pathlib import Path


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
        prog="cli.py",
        description="Convert documents between formats (markdown, Word, PDF).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python cli.py -i README.md -o README.docx\n"
            "  python cli.py --input report.pdf --output report.docx\n"
            "  python cli.py README.md README.docx\n"
            "  python cli.py -i README.md\n"
            "  python cli.py -i notes.md --to pdf\n"
            "  python cli.py --list"
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
        "-o",
        "--output",
        type=Path,
        dest="output_path",
        metavar="PATH",
        help="Path to the output file",
    )
    parser.add_argument(
        "--to",
        dest="dest_format",
        metavar="FORMAT",
        help="Output format extension (e.g. docx, pdf, md). "
        "When --output is omitted, the file is written next to the input "
        "with this extension (or a default for the input type).",
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
        metavar="OUTPUT",
        help="Output file path (alternative to --output)",
    )
    return parser


def _default_destination(source: Path, dest_format: str | None = None) -> Path:
    from core.converter.registry import default_destination_path

    return default_destination_path(source, dest_format)


def _resolve_paths(args: argparse.Namespace) -> tuple[Path | None, Path | None]:
    source = args.input_path or args.source
    destination = args.output_path or args.destination
    return source, destination


def _run_convert(args: argparse.Namespace) -> int:
    from core.converter.registry import get_converter

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
    from core.converter.registry import list_conversions

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
