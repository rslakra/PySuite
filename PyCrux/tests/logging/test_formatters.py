"""Tests for ``pycrux.logging.formatters`` — text, JSON and XML formatters and the factory."""

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pycrux.logging import (
    EventFormatter,
    ExceptionInfo,
    FormatterFactory,
    JsonFormatter,
    LogEvent,
    LogFormat,
    TextFormatter,
    XmlFormatter,
)
from pycrux.logging.formatters import DEFAULT_TEXT_PATTERN, _View

from .conftest import make_record


def _event(**overrides) -> LogEvent:
    fields = dict(
        timestamp="2024-01-02T03:04:05.000Z",
        level="INFO",
        level_no=20,
        logger="app.core",
        message="hello",
        module="mod",
        function="fn",
        line=7,
        path="/p/mod.py",
        thread="MainThread",
        thread_id=1,
        process=99,
    )
    fields.update(overrides)
    return LogEvent(**fields)


def _failing() -> RuntimeError:
    try:
        try:
            raise KeyError("root")
        except KeyError as exc:
            raise RuntimeError("top") from exc
    except RuntimeError as exc:
        return exc
    raise AssertionError("unreachable")


# --- EventFormatter --------------------------------------------------------------


def test_event_formatter_render_is_abstract() -> None:
    with pytest.raises(NotImplementedError):
        EventFormatter().render(_event())


def test_event_formatter_format_builds_event_from_record() -> None:
    class Echo(EventFormatter):
        def render(self, event: LogEvent) -> str:
            return f"{event.level}:{event.message}"

    assert Echo().format(make_record("hi %s", args=("you",), level=logging.ERROR)) == "ERROR:hi you"


def test_event_formatter_passes_include_stack_trace() -> None:
    exc = _failing()
    record = make_record(exc_info=(type(exc), exc, exc.__traceback__))
    slim = JsonFormatter(include_stack_trace=False).format(record)
    full = JsonFormatter().format(record)
    assert "stack_trace" not in json.loads(slim)["exception"]
    assert "stack_trace" in json.loads(full)["exception"]


# --- _View -----------------------------------------------------------------------


def test_view_renders_pairs_and_empty() -> None:
    assert str(_View()) == ""
    assert str(_View({"a": 1, "b": "x"})) == "[a=1, b=x]"


def test_view_missing_key_is_empty_string() -> None:
    assert _View({"a": 1})["zzz"] == ""


# --- TextFormatter ---------------------------------------------------------------


def test_text_formatter_default_pattern() -> None:
    assert TextFormatter().pattern == DEFAULT_TEXT_PATTERN
    line = TextFormatter().render(_event())
    assert line == "2024-01-02T03:04:05.000Z INFO     [MainThread] app.core - hello"


def test_text_formatter_includes_mdc_and_extra() -> None:
    line = TextFormatter().render(_event(mdc={"requestId": "r1"}, extra={"k": 5}))
    assert line.endswith("hello [requestId=r1] [k=5]")


def test_text_formatter_custom_pattern_fields() -> None:
    fmt = TextFormatter("{level}|{logger}|{module}.{function}:{line}|{path}|{thread_id}|{process}|{mdc[requestId]}|{mdc[nope]}|")
    assert fmt.render(_event(mdc={"requestId": "r1"})) == "INFO|app.core|mod.fn:7|/p/mod.py|1|99|r1||"


@pytest.mark.parametrize("pattern", ["{unknown}", "{message", "{}", "{mdc.attribute}"])
def test_text_formatter_rejects_invalid_pattern(pattern: str) -> None:
    with pytest.raises(ValueError, match="Invalid text log pattern"):
        TextFormatter(pattern)


def test_text_formatter_appends_stack_info() -> None:
    line = TextFormatter("{message}").render(_event(stack_info="Stack (most recent call last):\n  frame\n"))
    assert line == "hello\nStack (most recent call last):\n  frame"


def test_text_formatter_appends_stack_trace_and_root_cause() -> None:
    exc = ExceptionInfo.from_exception(_failing())
    text = TextFormatter("{message}").render(_event(exception=exc))
    assert "Traceback (most recent call last)" in text
    assert text.splitlines()[-1] == "Root cause: KeyError: 'root'"


def test_text_formatter_without_stack_trace_prints_type_and_message() -> None:
    exc = ExceptionInfo.from_exception(ValueError("bad"), include_stack_trace=False)
    assert TextFormatter("{message}").render(_event(exception=exc)) == "hello\nValueError: bad"


def test_text_formatter_format_end_to_end() -> None:
    exc = _failing()
    record = make_record("failed", level=logging.ERROR, exc_info=(type(exc), exc, exc.__traceback__))
    out = TextFormatter().format(record)
    assert "ERROR" in out and "failed" in out and "Root cause: KeyError" in out


# --- JsonFormatter ---------------------------------------------------------------


def test_json_formatter_is_compact_single_line() -> None:
    out = JsonFormatter().render(_event(mdc={"a": 1}))
    assert "\n" not in out
    assert ", " not in out and ": " not in out
    data = json.loads(out)
    assert data["message"] == "hello" and data["mdc"] == {"a": 1}


def test_json_formatter_keeps_unicode_and_stringifies_unknown_types() -> None:
    out = JsonFormatter().render(_event(message="héllo ✓", extra={"path": Path("/x")}))
    assert "héllo ✓" in out
    assert json.loads(out)["extra"] == {"path": "/x"}


# --- XmlFormatter ----------------------------------------------------------------


def test_xml_formatter_basic_structure() -> None:
    root = ET.fromstring(XmlFormatter().render(_event()))
    assert root.tag == "event"
    assert root.attrib == {"timestamp": "2024-01-02T03:04:05.000Z", "level": "INFO", "logger": "app.core"}
    assert root.findtext("message") == "hello"
    assert root.find("source").attrib == {"module": "mod", "function": "fn", "line": "7", "path": "/p/mod.py"}
    assert root.find("thread").attrib == {"name": "MainThread", "id": "1"}
    assert root.findtext("process") == "99"
    assert root.find("mdc") is None and root.find("extra") is None and root.find("exception") is None


def test_xml_formatter_mdc_and_extra_entries() -> None:
    root = ET.fromstring(
        XmlFormatter().render(_event(mdc={"requestId": "r1"}, extra={"payload": {"a": [1, 2]}, "n": 5, "t": (1, 2)}))
    )
    assert {e.get("key"): e.text for e in root.find("mdc")} == {"requestId": "r1"}
    extra = {e.get("key"): e.text for e in root.find("extra")}
    assert json.loads(extra["payload"]) == {"a": [1, 2]}
    assert extra["n"] == "5"
    assert json.loads(extra["t"]) == [1, 2]


def test_xml_formatter_stack_info() -> None:
    root = ET.fromstring(XmlFormatter().render(_event(stack_info="stack text")))
    assert root.findtext("stackInfo") == "stack text"


def test_xml_formatter_exception_with_causes_and_frames() -> None:
    exc = ExceptionInfo.from_exception(_failing())
    root = ET.fromstring(XmlFormatter().render(_event(exception=exc)))
    node = root.find("exception")
    assert node.get("type") == "RuntimeError"
    assert node.findtext("message") == "top"
    assert "Traceback" in node.findtext("stackTrace")
    frames = node.find("frames")
    assert frames is not None and frames[-1].get("function") == "_failing"
    cause = node.find("causes/cause")
    assert (cause.get("type"), cause.get("relation")) == ("KeyError", "cause")
    assert cause.findtext("message") == "'root'"
    assert cause.find("frames") is not None


def test_xml_formatter_exception_without_stack_trace_or_causes() -> None:
    exc = ExceptionInfo.from_exception(ValueError("bad"), include_stack_trace=False)
    node = ET.fromstring(XmlFormatter().render(_event(exception=exc))).find("exception")
    assert node.findtext("message") == "bad"
    assert node.find("stackTrace") is None and node.find("frames") is None and node.find("causes") is None


def test_xml_formatter_replaces_illegal_characters() -> None:
    out = XmlFormatter().render(_event(message="bad\x00char\x0b", extra={"k\x01": "v\x1f"}))
    root = ET.fromstring(out)  # would raise on illegal characters
    assert root.findtext("message") == "bad\ufffdchar\ufffd"
    assert root.find("extra")[0].get("key") == "k\ufffd"


def test_xml_clean_and_value_text_helpers() -> None:
    assert XmlFormatter._clean(5) == "5"
    assert XmlFormatter._clean("ok") == "ok"
    assert XmlFormatter._value_text({"a": 1}) == '{"a": 1}'
    assert XmlFormatter._value_text([1, "é"]) == '[1, "é"]'
    assert XmlFormatter._value_text(None) == "None"


# --- FormatterFactory ------------------------------------------------------------


@pytest.mark.parametrize(
    ("fmt", "cls"),
    [
        ("text", TextFormatter),
        (LogFormat.TEXT, TextFormatter),
        ("json", JsonFormatter),
        (LogFormat.JSON, JsonFormatter),
        ("xml", XmlFormatter),
        ("ndjson", JsonFormatter),
    ],
)
def test_factory_creates_matching_formatter(fmt, cls) -> None:
    assert type(FormatterFactory.create(fmt)) is cls


def test_factory_passes_pattern_and_stack_trace_flag() -> None:
    text = FormatterFactory.create("text", pattern="{message}", include_stack_trace=False)
    assert isinstance(text, TextFormatter)
    assert text.pattern == "{message}" and text.include_stack_trace is False
    assert FormatterFactory.create("json", pattern="ignored").include_stack_trace is True


def test_factory_rejects_unknown_format() -> None:
    with pytest.raises(ValueError):
        FormatterFactory.create("yaml")
