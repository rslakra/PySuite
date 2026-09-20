#!/usr/bin/env python3
"""
Unified CLI for Vestwell tenant tools (platform Excel export and agent roster).

Run from the **PoCSuite** repo root (or anywhere); ``sys.path`` is adjusted so
``common.*`` and ``tenants.vestwell.*`` resolve.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

# Bootstrap: allow `core.*` imports when run as `python office/main.py`
_pycore_root = Path(__file__).resolve().parents[1]
if str(_pycore_root) not in sys.path:
    sys.path.insert(0, str(_pycore_root))

from core.io.paths import PathUtils

# PoCSuite repo root; under PyCore layout ``office/main.py`` is one level below project root
_SRC_ROOT = PathUtils.ensure_package_root_for_file(__file__, ancestor_levels=2)


def _src_root() -> Path:
    return _SRC_ROOT


def _load_agent_roster_module() -> Any:
    path = _src_root() / "tenants" / "vestwell" / "agent_roster_handler.py"
    spec = importlib.util.spec_from_file_location("agent_roster_handler", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load agent roster from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cmd_export(args: argparse.Namespace) -> int:
    from tenants.vestwell.platform_data_handler import export_workbook

    xlsx: Path = args.xlsx
    if xlsx.name.startswith("~$"):
        print(
            "Refusing to read Excel lock file (~$...). Close Excel and use the real workbook.",
            file=sys.stderr,
        )
        return 2
    out = args.output_dir
    if out is None:
        out = xlsx.parent / f"{xlsx.stem}_json"
    paths = export_workbook(xlsx, out, pretty=args.pretty)
    for p in paths:
        print(p)
    return 0


def _open_roster(workbook: Path | None):
    mod = _load_agent_roster_module()
    return mod.AgentRoster(workbook)


def _cmd_roster_list(args: argparse.Namespace) -> int:
    with _open_roster(args.workbook) as roster:
        for name in roster.sheet_names():
            print(name)
    return 0


def _write_frame_csv(path: Path | None, text: str) -> None:
    if path is None:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    else:
        path.write_text(text, encoding="utf-8")


def _cmd_roster_merge(args: argparse.Namespace) -> int:
    sheets = list(args.sheets) if args.sheets else []
    with _open_roster(args.workbook) as roster:
        if args.format == "json":
            path = roster.write_merged_records_json(
                *sheets,
                output_path=args.output,
                dedupe_key=args.dedupe_key,
                keep=args.keep,
                pretty=args.pretty,
            )
            print(path)
            return 0
        if sheets:
            df = roster.merge_records(
                *sheets,
                dedupe_key=args.dedupe_key,
                keep=args.keep,
            )
        else:
            df = roster.merge_records(
                dedupe_key=args.dedupe_key,
                keep=args.keep,
            )
    csv = df.to_csv(index=False, lineterminator="\n")
    _write_frame_csv(args.output, csv)
    return 0


def _cmd_roster_merge_join(args: argparse.Namespace) -> int:
    sheets = list(args.sheets) if args.sheets else []
    with _open_roster(args.workbook) as roster:
        if args.format == "json":
            path = roster.write_merged_join_json(
                *sheets,
                output_path=args.output,
                on=args.on,
                how=args.how,
                pretty=args.pretty,
            )
            print(path)
            return 0
        if sheets:
            df = roster.merge_join(
                *sheets,
                on=args.on,
                how=args.how,
            )
        else:
            df = roster.merge_join(on=args.on, how=args.how)
    csv = df.to_csv(index=False, lineterminator="\n")
    _write_frame_csv(args.output, csv)
    return 0


def _cmd_roster_peek(args: argparse.Namespace) -> int:
    with _open_roster(args.workbook) as roster:
        df = roster.read_sheet(args.sheet, header_row=args.header_row)
    df = df.head(args.rows)
    csv = df.to_csv(index=False, lineterminator="\n")
    _write_frame_csv(args.output, csv)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Vestwell tools: export Platform Data workbooks to JSON; query agent roster.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    pe = sub.add_parser(
        "export",
        help="Export each Excel sheet to NDJSON (see tenants/vestwell/platform_data_handler.py).",
    )
    pe.add_argument(
        "xlsx",
        type=Path,
        help="Path to the .xlsx workbook",
    )
    pe.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: <xlsx_stem>_json next to the workbook)",
    )
    pe.add_argument(
        "--pretty",
        action="store_true",
        help="Write pretty JSON arrays instead of NDJSON",
    )
    pe.set_defaults(func=_cmd_export)

    pr = sub.add_parser(
        "roster", help="Agent roster workbook (dim_agent-style sheets)."
    )
    rsub = pr.add_subparsers(dest="roster_cmd", required=True)

    pl = rsub.add_parser("list", help="Print all sheet names in the workbook.")
    pl.add_argument(
        "-w",
        "--workbook",
        type=Path,
        default=None,
        help="Path to roster .xlsx (default: bundled Source of Truth under tenants/vestwell/data/Agent Roster/)",
    )
    pl.set_defaults(func=_cmd_roster_list)

    pm = rsub.add_parser(
        "merge",
        help="Concatenate sheets and dedupe by key (default key: zendesk_agent_id).",
    )
    pm.add_argument(
        "sheets",
        nargs="*",
        help="Sheet names to stack (omit to use default dim_agent only)",
    )
    pm.add_argument(
        "-w",
        "--workbook",
        type=Path,
        default=None,
        help="Path to roster .xlsx (default: bundled Source of Truth under tenants/vestwell/data/Agent Roster/)",
    )
    pm.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path: for csv, default stdout; for json, default <workbook_stem>_merged.json",
    )
    pm.add_argument(
        "--format",
        choices=("csv", "json"),
        default="csv",
        help="csv (default) or json (NDJSON via agent roster writer)",
    )
    pm.add_argument(
        "--pretty",
        action="store_true",
        help="With --format json, write one pretty JSON array instead of NDJSON",
    )
    pm.add_argument(
        "--dedupe-key",
        default="zendesk_agent_id",
        help="Column for drop_duplicates (default: zendesk_agent_id)",
    )
    pm.add_argument(
        "--keep",
        choices=("first", "last"),
        default="last",
        help="When duplicate keys exist, keep first or last row (default: last)",
    )
    pm.set_defaults(func=_cmd_roster_merge)

    pj = rsub.add_parser(
        "merge-join",
        help="Successive pandas merges on a key across sheets.",
    )
    pj.add_argument(
        "sheets",
        nargs="*",
        help="Sheet names (omit for default dim_agent only)",
    )
    pj.add_argument(
        "-w",
        "--workbook",
        type=Path,
        default=None,
        help="Path to roster .xlsx (default: bundled Source of Truth under tenants/vestwell/data/Agent Roster/)",
    )
    pj.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path: for csv, default stdout; for json, default <workbook_stem>_merge_join.json",
    )
    pj.add_argument(
        "--format",
        choices=("csv", "json"),
        default="csv",
        help="csv (default) or json (NDJSON via agent roster writer)",
    )
    pj.add_argument(
        "--pretty",
        action="store_true",
        help="With --format json, write one pretty JSON array instead of NDJSON",
    )
    pj.add_argument(
        "--on",
        default="zendesk_agent_id",
        help="Merge key column (default: zendesk_agent_id)",
    )
    pj.add_argument(
        "--how",
        choices=("left", "right", "outer", "inner", "cross"),
        default="outer",
        help="Merge how (default: outer)",
    )
    pj.set_defaults(func=_cmd_roster_merge_join)

    pk = rsub.add_parser(
        "peek",
        help="Load one sheet (auto header for dim_agent layout) and print first rows as CSV.",
    )
    pk.add_argument("sheet", help="Sheet name, e.g. dim_agent")
    pk.add_argument(
        "-w",
        "--workbook",
        type=Path,
        default=None,
        help="Path to roster .xlsx (default: bundled Source of Truth under tenants/vestwell/data/Agent Roster/)",
    )
    pk.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write CSV here (default: print to stdout)",
    )
    pk.add_argument(
        "--rows",
        type=int,
        default=10,
        help="Number of data rows to show (default: 10)",
    )
    pk.add_argument(
        "--header-row",
        type=int,
        default=None,
        help="0-based Excel header row; omit for auto-detect (dim_agent style)",
    )
    pk.set_defaults(func=_cmd_roster_peek)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 2
    return int(func(args))


if __name__ == "__main__":
    raise SystemExit(main())
