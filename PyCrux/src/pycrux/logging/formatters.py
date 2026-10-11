"""Text, JSON and XML formatters.

Every formatter turns a ``LogRecord`` into a :class:`~pycrux.logging.events.LogEvent`
and renders it, so all formats carry the same information: message, source,
thread, MDC, extras and the complete exception (stack trace + cause chain).
"""

from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any

from .events import LogEvent
from .types import LogFormat

DEFAULT_TEXT_PATTERN = "{timestamp} {level:<8} [{thread}] {logger} - {message} {mdc} {extra}"


class EventFormatter(logging.Formatter):
    """Base class: builds a ``LogEvent`` and delegates rendering to :meth:`render`."""

    def __init__(self, *, include_stack_trace: bool = True) -> None:
        super().__init__()
        self.include_stack_trace = include_stack_trace

    def format(self, record: logging.LogRecord) -> str:
        return self.render(LogEvent.from_record(record, include_stack_trace=self.include_stack_trace))

    def render(self, event: LogEvent) -> str:  # pragma: no cover - abstract
        raise NotImplementedError


class _View(dict):
    """Dict rendered as ``[k=v, k=v]`` (empty string when empty); missing keys give ``""``.

    Lets a text pattern use ``{mdc}`` for everything or ``{mdc[requestId]}`` for one key.
    """

    def __missing__(self, key: str) -> str:
        return ""

    def __str__(self) -> str:
        if not self:
            return ""
        return "[" + ", ".join(f"{k}={v}" for k, v in self.items()) + "]"


class TextFormatter(EventFormatter):
    """Human-readable single-line format followed by the full stack trace.

    ``pattern`` is a :meth:`str.format` string. Available fields: ``timestamp``,
    ``level``, ``logger``, ``message``, ``module``, ``function``, ``line``,
    ``path``, ``thread``, ``thread_id``, ``process``, ``mdc`` and ``extra``
    (``{mdc[requestId]}`` selects a single MDC key).
    """

    def __init__(self, pattern: str | None = None, *, include_stack_trace: bool = True) -> None:
        super().__init__(include_stack_trace=include_stack_trace)
        self.pattern = pattern or DEFAULT_TEXT_PATTERN
        self._validate_pattern()

    def _validate_pattern(self) -> None:
        sample = LogEvent(
            timestamp="", level="INFO", level_no=20, logger="", message="", module="",
            function="", line=0, path="", thread="", thread_id=0, process=0,
        )
        try:
            self.pattern.format(**self._fields(sample))
        except (KeyError, IndexError, ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid text log pattern {self.pattern!r}: {exc!r}") from exc

    @staticmethod
    def _fields(event: LogEvent) -> dict[str, Any]:
        return {
            "timestamp": event.timestamp,
            "level": event.level,
            "logger": event.logger,
            "message": event.message,
            "module": event.module,
            "function": event.function,
            "line": event.line,
            "path": event.path,
            "thread": event.thread,
            "thread_id": event.thread_id,
            "process": event.process,
            "mdc": _View(event.mdc),
            "extra": _View(event.extra),
        }

    def render(self, event: LogEvent) -> str:
        lines = [self.pattern.format(**self._fields(event)).rstrip()]
        if event.stack_info:
            lines.append(event.stack_info.rstrip("\n"))
        exc = event.exception
        if exc is not None:
            lines.append(exc.stack_trace.rstrip("\n") if exc.stack_trace else f"{exc.type}: {exc.message}")
            root = exc.root_cause
            if root is not None:
                lines.append(f"Root cause: {root.type}: {root.message}")
        return "\n".join(lines)


class JsonFormatter(EventFormatter):
    """One compact JSON object per line (JSON Lines)."""

    def render(self, event: LogEvent) -> str:
        return json.dumps(event.to_dict(), default=str, ensure_ascii=False, separators=(",", ":"))


class XmlFormatter(EventFormatter):
    """One ``<event>`` element per record.

    Events are written as a fragment stream (like Log4j's ``XMLLayout``); wrap the
    file content in a root element to parse it as a single XML document.
    """

    # Characters that are not allowed in XML 1.0 documents.
    _ILLEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")

    def render(self, event: LogEvent) -> str:
        return ET.tostring(self._build(event.to_dict()), encoding="unicode")

    def _build(self, data: dict[str, Any]) -> ET.Element:
        clean = self._clean
        root = ET.Element(
            "event",
            {
                "timestamp": clean(data["timestamp"]),
                "level": clean(data["level"]),
                "logger": clean(data["logger"]),
            },
        )
        self._text_child(root, "message", data["message"])
        ET.SubElement(root, "source", {k: clean(v) for k, v in data["source"].items()})
        thread = data["thread"]
        ET.SubElement(root, "thread", {"name": clean(thread["name"]), "id": clean(thread["id"])})
        self._text_child(root, "process", data["process"])
        for name in ("mdc", "extra"):
            entries = data.get(name)
            if entries:
                parent = ET.SubElement(root, name)
                for key, value in entries.items():
                    self._text_child(parent, "entry", self._value_text(value), {"key": clean(key)})
        if "stack_info" in data:
            self._text_child(root, "stackInfo", data["stack_info"])
        if "exception" in data:
            self._exception(root, data["exception"])
        return root

    def _exception(self, parent: ET.Element, exc: dict[str, Any]) -> None:
        clean = self._clean
        node = ET.SubElement(parent, "exception", {"type": clean(exc["type"])})
        self._text_child(node, "message", exc["message"])
        if "stack_trace" in exc:
            self._text_child(node, "stackTrace", exc["stack_trace"])
        self._frames(node, exc.get("frames"))
        causes = exc.get("causes")
        if causes:
            container = ET.SubElement(node, "causes")
            for cause in causes:
                item = ET.SubElement(
                    container,
                    "cause",
                    {"type": clean(cause["type"]), "relation": clean(cause["relation"])},
                )
                self._text_child(item, "message", cause["message"])
                self._frames(item, cause.get("frames"))

    def _frames(self, parent: ET.Element, frames: list[dict[str, Any]] | None) -> None:
        if not frames:
            return
        clean = self._clean
        container = ET.SubElement(parent, "frames")
        for frame in frames:
            node = ET.SubElement(
                container,
                "frame",
                {
                    "file": clean(frame["file"]),
                    "line": clean(frame["line"]),
                    "function": clean(frame["function"]),
                },
            )
            node.text = clean(frame["code"])

    def _text_child(
        self, parent: ET.Element, tag: str, value: Any, attrs: dict[str, str] | None = None
    ) -> ET.Element:
        node = ET.SubElement(parent, tag, attrs or {})
        node.text = self._clean(value)
        return node

    @staticmethod
    def _value_text(value: Any) -> str:
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, default=str, ensure_ascii=False)
        return str(value)

    @classmethod
    def _clean(cls, value: Any) -> str:
        """Replace characters that are illegal in XML with U+FFFD."""
        return cls._ILLEGAL.sub("\ufffd", str(value))


class FormatterFactory:
    """Creates the formatter for a :class:`LogFormat`."""

    @staticmethod
    def create(
        fmt: LogFormat | str,
        *,
        pattern: str | None = None,
        include_stack_trace: bool = True,
    ) -> EventFormatter:
        """Create the formatter for ``fmt`` (``pattern`` only applies to ``text``)."""
        fmt = LogFormat.from_string(fmt)
        if fmt is LogFormat.JSON:
            return JsonFormatter(include_stack_trace=include_stack_trace)
        if fmt is LogFormat.XML:
            return XmlFormatter(include_stack_trace=include_stack_trace)
        return TextFormatter(pattern, include_stack_trace=include_stack_trace)
