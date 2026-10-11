"""Tests for ``pycrux.logging.events`` — frames, cause chains, exception info, log events."""

import json
import logging

from pycrux.logging import MDC, CauseInfo, ExceptionInfo, LogEvent, StackFrame

from .conftest import make_record


class CustomError(Exception):
    """Defined at module level so its qualified name is predictable."""


def _failing() -> RuntimeError:
    """Return a RuntimeError -> ValueError -> KeyError chain linked with ``raise ... from``."""
    try:
        try:
            try:
                raise KeyError("root")
            except KeyError as exc:
                raise ValueError("mid") from exc
        except ValueError as exc:
            raise RuntimeError("top") from exc
    except RuntimeError as exc:
        return exc
    raise AssertionError("unreachable")


def _implicit_context() -> ValueError:
    try:
        try:
            raise KeyError("first")
        except KeyError:
            raise ValueError("second")  # noqa: B904 - implicit chaining is the point
    except ValueError as exc:
        return exc
    raise AssertionError("unreachable")


# --- StackFrame ------------------------------------------------------------------


def test_stack_frame_from_exception_outermost_first() -> None:
    frames = StackFrame.from_exception(_failing())
    assert frames
    assert all(isinstance(f, StackFrame) for f in frames)
    assert frames[-1].function == "_failing"
    assert frames[-1].file.endswith("test_events.py")
    assert frames[-1].line > 0
    assert "raise RuntimeError" in frames[-1].code


def test_stack_frame_from_exception_without_traceback() -> None:
    assert StackFrame.from_exception(ValueError("never raised")) == ()


def test_stack_frame_to_dict() -> None:
    frame = StackFrame(file="f.py", line=3, function="fn", code="x = 1")
    assert frame.to_dict() == {"file": "f.py", "line": 3, "function": "fn", "code": "x = 1"}
    assert StackFrame("f.py", 1, "fn").code == ""


# --- CauseInfo -------------------------------------------------------------------


def test_cause_info_from_exception_with_and_without_stack() -> None:
    exc = _failing()
    with_stack = CauseInfo.from_exception(exc, "cause")
    without = CauseInfo.from_exception(exc, "context", include_stack_trace=False)
    assert (with_stack.type, with_stack.message, with_stack.relation) == ("RuntimeError", "top", "cause")
    assert with_stack.frames
    assert without.frames == () and without.relation == "context"


def test_cause_info_to_dict_omits_empty_frames() -> None:
    bare = CauseInfo(type="E", message="m", relation="cause")
    assert bare.to_dict() == {"type": "E", "message": "m", "relation": "cause"}

    framed = CauseInfo("E", "m", "cause", (StackFrame("f.py", 1, "fn"),))
    assert framed.to_dict()["frames"] == [{"file": "f.py", "line": 1, "function": "fn", "code": ""}]


# --- ExceptionInfo ---------------------------------------------------------------


def test_type_name_omits_builtins_but_qualifies_others() -> None:
    assert ExceptionInfo.type_name(ValueError("x")) == "ValueError"
    assert ExceptionInfo.type_name(json.JSONDecodeError("m", "d", 0)) == "json.decoder.JSONDecodeError"
    assert ExceptionInfo.type_name(CustomError()) == f"{__name__}.CustomError"


def test_from_exception_collects_cause_chain_down_to_root() -> None:
    info = ExceptionInfo.from_exception(_failing())
    assert (info.type, info.message) == ("RuntimeError", "top")
    assert [(c.type, c.relation) for c in info.causes] == [("ValueError", "cause"), ("KeyError", "cause")]
    assert info.root_cause is info.causes[-1]
    assert info.root_cause.message == "'root'"
    assert "Traceback" in info.stack_trace
    assert "KeyError" in info.stack_trace  # chained exceptions are part of the formatted trace
    assert info.frames


def test_from_exception_without_stack_trace() -> None:
    info = ExceptionInfo.from_exception(_failing(), include_stack_trace=False)
    assert info.stack_trace == ""
    assert info.frames == ()
    assert all(c.frames == () for c in info.causes)
    assert len(info.causes) == 2


def test_root_cause_is_none_without_a_cause() -> None:
    info = ExceptionInfo.from_exception(ValueError("alone"))
    assert info.causes == ()
    assert info.root_cause is None


def test_implicit_context_is_reported_as_context() -> None:
    info = ExceptionInfo.from_exception(_implicit_context())
    assert [(c.type, c.relation) for c in info.causes] == [("KeyError", "context")]


def test_suppressed_context_is_not_followed() -> None:
    try:
        try:
            raise KeyError("hidden")
        except KeyError:
            raise ValueError("visible") from None
    except ValueError as exc:
        info = ExceptionInfo.from_exception(exc)
    assert info.causes == ()


def test_cyclic_cause_chain_terminates() -> None:
    first, second = ValueError("first"), KeyError("second")
    first.__cause__ = second
    second.__cause__ = first
    info = ExceptionInfo.from_exception(first)
    assert [c.type for c in info.causes] == ["KeyError"]


def test_cause_chain_depth_is_capped() -> None:
    chain = [ValueError(f"e{i}") for i in range(30)]
    for current, nxt in zip(chain, chain[1:]):
        current.__cause__ = nxt
    info = ExceptionInfo.from_exception(chain[0])
    assert len(info.causes) == 20
    assert info.causes[0].message == "e1"


def test_exception_info_to_dict() -> None:
    minimal = ExceptionInfo(type="E", message="m")
    assert minimal.to_dict() == {"type": "E", "message": "m"}

    full = ExceptionInfo.from_exception(_failing()).to_dict()
    assert {"type", "message", "stack_trace", "frames", "causes"} <= set(full)
    assert [c["type"] for c in full["causes"]] == ["ValueError", "KeyError"]
    json.dumps(full)  # must be JSON serialisable


# --- LogEvent --------------------------------------------------------------------


def test_from_record_basic_fields() -> None:
    record = make_record("hello %s", args=("world",), level=logging.WARNING, name="a.b")
    record.created = 0
    event = LogEvent.from_record(record)

    assert event.timestamp == "1970-01-01T00:00:00.000Z"
    assert (event.level, event.level_no) == ("WARNING", logging.WARNING)
    assert event.logger == "a.b"
    assert event.message == "hello world"
    assert (event.module, event.function, event.line, event.path) == ("sample", "test_func", 42, "/tmp/sample.py")
    assert event.thread == record.threadName
    assert event.thread_id == record.thread
    assert event.process == record.process
    assert event.mdc == {} and event.extra == {}
    assert event.exception is None and event.stack_info is None


def test_from_record_uses_record_mdc_when_present() -> None:
    MDC.put("current", 1)
    record = make_record()
    record.mdc = {"snapshot": 2}
    event = LogEvent.from_record(record)
    assert event.mdc == {"snapshot": 2}
    assert "mdc" not in event.extra


def test_from_record_falls_back_to_current_mdc() -> None:
    MDC.put("current", 1)
    assert LogEvent.from_record(make_record()).mdc == {"current": 1}


def test_from_record_collects_extra_attributes() -> None:
    record = make_record()
    record.order_id = 7
    assert LogEvent.from_record(record).extra == {"order_id": 7}


def test_from_record_with_exception_and_stack_info() -> None:
    exc = _failing()
    record = make_record(exc_info=(type(exc), exc, exc.__traceback__))
    record.stack_info = "Stack (most recent call last): ..."

    event = LogEvent.from_record(record)
    assert event.exception is not None and event.exception.type == "RuntimeError"
    assert event.stack_info == record.stack_info

    slim = LogEvent.from_record(record, include_stack_trace=False)
    assert slim.exception is not None and slim.exception.stack_trace == ""
    assert slim.stack_info is None


def test_from_record_ignores_empty_exc_info() -> None:
    record = make_record(exc_info=(None, None, None))
    assert LogEvent.from_record(record).exception is None


def test_to_dict_minimal_omits_empty_parts() -> None:
    data = LogEvent.from_record(make_record()).to_dict()
    assert set(data) == {"timestamp", "level", "logger", "message", "source", "thread", "process"}
    assert data["source"] == {"module": "sample", "function": "test_func", "line": 42, "path": "/tmp/sample.py"}
    assert set(data["thread"]) == {"name", "id"}


def test_to_dict_includes_optional_parts_when_present() -> None:
    exc = _failing()
    record = make_record(exc_info=(type(exc), exc, exc.__traceback__))
    record.mdc = {"requestId": "r1"}
    record.custom = "x"
    record.stack_info = "stack"

    data = LogEvent.from_record(record).to_dict()
    assert data["mdc"] == {"requestId": "r1"}
    assert data["extra"] == {"custom": "x"}
    assert data["stack_info"] == "stack"
    assert data["exception"]["type"] == "RuntimeError"
