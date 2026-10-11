"""Logging configuration model."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .types import LogFormat, LogTarget

_STREAMS = ("stdout", "stderr")


@dataclass
class OutputConfig:
    """One log destination: where it writes, in which format, at which level.

    Attributes:
        format: ``text`` (``.txt``), ``json`` (``.json``) or ``xml`` (``.xml``).
        target: ``console`` or ``file``.
        path: File path for ``file`` targets. A path without an extension gets the
            format's extension (``logs/app`` -> ``logs/app.json``).
        level: Minimum level for this destination (``None`` = logger level).
        stream: ``stdout`` or ``stderr`` for ``console`` targets.
        pattern: ``str.format`` pattern for the ``text`` format.
        max_bytes: Rotate the file after this many bytes (``0`` = never rotate).
        backup_count: Number of rotated files to keep.
        encoding: File encoding.
    """

    format: LogFormat = LogFormat.TEXT
    target: LogTarget = LogTarget.CONSOLE
    path: str | None = None
    level: int | None = None
    stream: str = "stderr"
    pattern: str | None = None
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5
    encoding: str = "utf-8"

    def __post_init__(self) -> None:
        self.format = LogFormat.from_string(self.format)
        self.target = LogTarget.from_string(self.target)
        if self.target is LogTarget.FILE and not self.path:
            raise ValueError("A 'file' output requires a 'path'")
        if self.stream not in _STREAMS:
            raise ValueError(f"Invalid stream {self.stream!r}; expected one of {_STREAMS}")
        if self.max_bytes < 0 or self.backup_count < 0:
            raise ValueError("'max_bytes' and 'backup_count' must not be negative")

    def resolved_path(self) -> Path | None:
        """The file path with the format's extension added when none was given."""
        if self.target is not LogTarget.FILE or not self.path:
            return None
        path = Path(self.path).expanduser()
        return path if path.suffix else path.with_suffix(self.format.extension)


@dataclass
class LogConfig:
    """Complete logging configuration.

    Attributes:
        level: Level of the configured logger (root by default).
        levels: Per-logger level overrides, e.g. ``{"urllib3": LogLevel.WARN}``.
        outputs: Log destinations; every event goes to each of them.
        mdc_keys: MDC keys to include in events (``None`` = all keys).
        mdc_defaults: Context entries added to every event (e.g. ``app``, ``env``);
            values in the MDC override them.
        include_stack_trace: Include full stack traces and frames for exceptions.
        capture_uncaught: Log uncaught exceptions (main thread and other threads)
            at ``CRITICAL`` with the complete stack before the program exits.
    """

    level: int = logging.INFO
    levels: dict[str, int] = field(default_factory=dict)
    outputs: list[OutputConfig] = field(default_factory=lambda: [OutputConfig()])
    mdc_keys: tuple[str, ...] | None = None
    mdc_defaults: dict[str, Any] = field(default_factory=dict)
    include_stack_trace: bool = True
    capture_uncaught: bool = False

    def __post_init__(self) -> None:
        if not self.outputs:
            raise ValueError("At least one output is required")
        if self.mdc_keys is not None:
            self.mdc_keys = tuple(self.mdc_keys) or None
