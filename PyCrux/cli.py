#!/usr/bin/env python3
"""Backward-compatible CLI entry point — delegates to ``pycrux.cli`` (requires ``make setup`` / an editable install)."""

from pycrux.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
