"""Structured log event model.

A :class:`LogEvent` is the format-independent representation of one log record;
the formatters render it as text, JSON or XML.
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .mdc import MDC

# Attributes every ``LogRecord`` has; anything else was passed via ``extra=``.
_STANDARD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "mdc",
    "taskName",
}

_MAX_CAUSE_DEPTH = 20


@dataclass(frozen=True)
class StackFrame:
    """One frame of a traceback."""

    file: str
    line: int
    function: str
    code: str = ""

    @classmethod
    def from_exception(cls, exc: BaseException) -> tuple[StackFrame, ...]:
        """Return the frames of ``exc``'s traceback, outermost call first."""
        return tuple(
            cls(file=f.filename, line=f.lineno or 0, function=f.name, code=f.line or "")
            for f in traceback.extract_tb(exc.__traceback__)
        )

    def to_dict(self) -> dict[str, Any]:
        return {"file": self.file, "line": self.line, "function": self.function, "code": self.code}


@dataclass(frozen=True)
class CauseInfo:
    """One link of an exception's cause chain."""

    type: str
    message: str
    relation: str  # "cause" (raise ... from ...) or "context" (raised while handling)
    frames: tuple[StackFrame, ...] = ()

    @classmethod
    def from_exception(
        cls, exc: BaseException, relation: str, *, include_stack_trace: bool = True
    ) -> CauseInfo:
        return cls(
            type=ExceptionInfo.type_name(exc),
            message=str(exc),
            relation=relation,
            frames=StackFrame.from_exception(exc) if include_stack_trace else (),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.type, "message": self.message, "relation": self.relation}
        if self.frames:
            data["frames"] = [frame.to_dict() for frame in self.frames]
        return data


@dataclass(frozen=True)
class ExceptionInfo:
    """An exception with its complete stack and cause chain.

    ``stack_trace`` is the full formatted traceback including every chained
    exception. ``causes`` lists the chain from the immediate cause down to the
    root cause (``root_cause`` is the last entry).
    """

    type: str
    message: str
    stack_trace: str = ""
    frames: tuple[StackFrame, ...] = ()
    causes: tuple[CauseInfo, ...] = field(default_factory=tuple)

    @staticmethod
    def type_name(exc: BaseException) -> str:
        """Qualified class name (``builtins`` and ``__main__`` are omitted)."""
        cls = type(exc)
        if cls.__module__ in ("builtins", "__main__"):
            return cls.__qualname__
        return f"{cls.__module__}.{cls.__qualname__}"

    @property
    def root_cause(self) -> CauseInfo | None:
        """The innermost cause, or ``None`` when the exception has no cause."""
        return self.causes[-1] if self.causes else None

    @classmethod
    def from_exception(cls, exc: BaseException, *, include_stack_trace: bool = True) -> ExceptionInfo:
        """Capture ``exc`` including its ``__cause__`` / ``__context__`` chain."""
        causes: list[CauseInfo] = []
        seen = {id(exc)}
        current = exc
        while len(causes) < _MAX_CAUSE_DEPTH:
            if current.__cause__ is not None:
                nxt, relation = current.__cause__, "cause"
            elif current.__context__ is not None and not current.__suppress_context__:
                nxt, relation = current.__context__, "context"
            else:
                break
            if id(nxt) in seen:
                break
            seen.add(id(nxt))
            causes.append(CauseInfo.from_exception(nxt, relation, include_stack_trace=include_stack_trace))
            current = nxt

        stack_trace = ""
        if include_stack_trace:
            stack_trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        return cls(
            type=cls.type_name(exc),
            message=str(exc),
            stack_trace=stack_trace,
            frames=StackFrame.from_exception(exc) if include_stack_trace else (),
            causes=tuple(causes),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.type, "message": self.message}
        if self.stack_trace:
            data["stack_trace"] = self.stack_trace
        if self.frames:
            data["frames"] = [frame.to_dict() for frame in self.frames]
        if self.causes:
            data["causes"] = [cause.to_dict() for cause in self.causes]
        return data


@dataclass(frozen=True)
class LogEvent:
    """Format-independent view of one log record."""

    timestamp: str
    level: str
    level_no: int
    logger: str
    message: str
    module: str
    function: str
    line: int
    path: str
    thread: str
    thread_id: int
    process: int
    mdc: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)
    exception: ExceptionInfo | None = None
    stack_info: str | None = None

    @classmethod
    def from_record(cls, record: logging.LogRecord, *, include_stack_trace: bool = True) -> LogEvent:
        """Build an event from a ``LogRecord``.

        The MDC snapshot is taken from ``record.mdc`` (set by ``MDCFilter``); if
        the record has none, the current MDC is used.
        """
        mdc = getattr(record, "mdc", None)
        if mdc is None:
            mdc = MDC.get_all()

        exception = None
        if record.exc_info and record.exc_info[1] is not None:
            exception = ExceptionInfo.from_exception(
                record.exc_info[1], include_stack_trace=include_stack_trace
            )

        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return cls(
            timestamp=timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            level=record.levelname,
            level_no=record.levelno,
            logger=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line=record.lineno,
            path=record.pathname,
            thread=record.threadName or "",
            thread_id=record.thread or 0,
            process=record.process or 0,
            mdc=dict(mdc),
            extra={k: v for k, v in record.__dict__.items() if k not in _STANDARD_ATTRS},
            exception=exception,
            stack_info=record.stack_info if include_stack_trace else None,
        )

    def to_dict(self) -> dict[str, Any]:
        """Plain-dict form used by the JSON and XML formatters (empty parts omitted)."""
        data: dict[str, Any] = {
            "timestamp": self.timestamp,
            "level": self.level,
            "logger": self.logger,
            "message": self.message,
            "source": {
                "module": self.module,
                "function": self.function,
                "line": self.line,
                "path": self.path,
            },
            "thread": {"name": self.thread, "id": self.thread_id},
            "process": self.process,
        }
        if self.mdc:
            data["mdc"] = dict(self.mdc)
        if self.extra:
            data["extra"] = dict(self.extra)
        if self.exception is not None:
            data["exception"] = self.exception.to_dict()
        if self.stack_info:
            data["stack_info"] = self.stack_info
        return data
