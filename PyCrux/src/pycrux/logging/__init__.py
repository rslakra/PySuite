"""Consistent, configurable application logging.

Stdlib-only layer over :mod:`logging` that adds text/JSON/XML output, a
Mapped Diagnostic Context (MDC), and complete exception capture.
"""

from .config import LogConfig, OutputConfig
from .events import CauseInfo, ExceptionInfo, LogEvent, StackFrame
from .formatters import (
    EventFormatter,
    FormatterFactory,
    JsonFormatter,
    TextFormatter,
    XmlFormatter,
)
from .logger import HandlerFactory, LogManager, MDCFilter, UncaughtExceptionHandler
from .mdc import MDC, MDCScope, RequestScope
from .parser import LogConfigParser
from .types import LogFormat, LogLevel, LogTarget

__all__ = [
    "CauseInfo",
    "EventFormatter",
    "ExceptionInfo",
    "FormatterFactory",
    "HandlerFactory",
    "JsonFormatter",
    "LogConfig",
    "LogConfigParser",
    "LogEvent",
    "LogFormat",
    "LogLevel",
    "LogManager",
    "LogTarget",
    "MDC",
    "MDCFilter",
    "MDCScope",
    "OutputConfig",
    "RequestScope",
    "StackFrame",
    "TextFormatter",
    "UncaughtExceptionHandler",
    "XmlFormatter",
]
