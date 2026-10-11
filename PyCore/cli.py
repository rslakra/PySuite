#!/usr/bin/env python3
"""Backward-compatible CLI entry point — delegates to ``core.cli``."""

from core.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
