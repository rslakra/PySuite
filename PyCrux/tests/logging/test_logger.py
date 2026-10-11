"""Tests for ``pycrux.logging.logger`` — ``MDCFilter``, ``HandlerFactory``, ``UncaughtExceptionHandler``, ``LogManager``."""

import json
import logging
import logging.handlers
import sys
import threading

import pytest

from pycrux.logging import (
    MDC,
    HandlerFactory,
    JsonFormatter,
    LogConfig,
    LogManager,
    MDCFilter,
    OutputConfig,
    TextFormatter,
    UncaughtExceptionHandler,
    XmlFormatter,
)

from .conftest import make_record

# --- MDCFilter -------------------------------------------------------------------


def test_filter_always_accepts_and_attaches_snapshot() -> None:
    MDC.put("a", 1)
    record = make_record()
    assert MDCFilter().filter(record) is True
    assert record.mdc == {"a": 1}


def test_filter_defaults_are_overridden_by_mdc() -> None:
    MDC.put("env", "prod")
    record = make_record()
    MDCFilter(defaults={"env": "dev", "app": "svc"}).filter(record)
    assert record.mdc == {"app": "svc", "env": "prod"}


def test_filter_keeps_only_requested_keys_in_order() -> None:
    MDC.put("a", 1)
    MDC.put("b", 2)
    MDC.put("c", 3)
    record = make_record()
    MDCFilter(keys=("c", "a", "missing")).filter(record)
    assert list(record.mdc.items()) == [("c", 3), ("a", 1)]


@pytest.mark.parametrize("keys", [None, ()])
def test_filter_without_keys_keeps_everything(keys) -> None:
    MDC.put("a", 1)
    record = make_record()
    MDCFilter(keys=keys).filter(record)
    assert record.mdc == {"a": 1}


# --- HandlerFactory --------------------------------------------------------------


def test_console_handler_uses_stderr_by_default(capsys) -> None:
    handler = HandlerFactory.create(OutputConfig(), LogConfig())
    assert type(handler) is logging.StreamHandler
    assert handler.stream is sys.stderr
    assert isinstance(handler.formatter, TextFormatter)


def test_console_handler_can_use_stdout(capsys) -> None:
    handler = HandlerFactory.create(OutputConfig(stream="stdout"), LogConfig())
    assert handler.stream is sys.stdout


def test_handler_level_and_formatter_options() -> None:
    cfg = LogConfig(include_stack_trace=False)
    handler = HandlerFactory.create(OutputConfig(format="json", level=logging.ERROR), cfg)
    assert handler.level == logging.ERROR
    assert isinstance(handler.formatter, JsonFormatter)
    assert handler.formatter.include_stack_trace is False


def test_handler_level_defaults_to_notset() -> None:
    assert HandlerFactory.create(OutputConfig(), LogConfig()).level == logging.NOTSET


def test_handler_uses_text_pattern() -> None:
    handler = HandlerFactory.create(OutputConfig(pattern="{message}"), LogConfig())
    assert handler.formatter.pattern == "{message}"


def test_handler_gets_mdc_filter_with_config_keys_and_defaults() -> None:
    cfg = LogConfig(mdc_keys=["a"], mdc_defaults={"app": "svc"})
    handler = HandlerFactory.create(OutputConfig(), cfg)
    (mdc_filter,) = handler.filters
    assert isinstance(mdc_filter, MDCFilter)
    assert mdc_filter._keys == ("a",)
    assert mdc_filter._defaults == {"app": "svc"}


def test_file_handler_is_rotating_lazy_and_creates_directories(tmp_path) -> None:
    out = OutputConfig(format="xml", target="file", path=str(tmp_path / "nested" / "dir" / "app"), max_bytes=123, backup_count=2)
    handler = HandlerFactory.create(out, LogConfig())
    try:
        assert isinstance(handler, logging.handlers.RotatingFileHandler)
        assert isinstance(handler.formatter, XmlFormatter)
        assert handler.maxBytes == 123 and handler.backupCount == 2
        assert handler.baseFilename == str(tmp_path / "nested" / "dir" / "app.xml")
        assert (tmp_path / "nested" / "dir").is_dir()
        assert not (tmp_path / "nested" / "dir" / "app.xml").exists()  # delay=True
    finally:
        handler.close()


# --- UncaughtExceptionHandler ----------------------------------------------------


def test_install_replaces_hooks_and_uninstall_restores_them(list_logger) -> None:
    before_sys, before_thread = sys.excepthook, threading.excepthook
    handler = UncaughtExceptionHandler(list_logger)
    assert handler.installed is False

    handler.install()
    assert handler.installed is True
    assert sys.excepthook is not before_sys
    assert threading.excepthook is not before_thread

    handler.uninstall()
    assert handler.installed is False
    assert sys.excepthook is before_sys
    assert threading.excepthook is before_thread


def test_install_is_idempotent(list_logger) -> None:
    original = sys.excepthook
    handler = UncaughtExceptionHandler(list_logger)
    handler.install()
    hook = sys.excepthook
    handler.install()
    assert sys.excepthook is hook
    handler.uninstall()
    assert sys.excepthook is original


def test_uninstall_without_install_is_a_noop(list_logger) -> None:
    before = sys.excepthook
    UncaughtExceptionHandler(list_logger).uninstall()
    assert sys.excepthook is before


def test_uninstall_does_not_clobber_hooks_installed_later(list_logger) -> None:
    handler = UncaughtExceptionHandler(list_logger)
    handler.install()

    def foreign_sys(*_args) -> None: ...

    def foreign_thread(_args) -> None: ...

    sys.excepthook, threading.excepthook = foreign_sys, foreign_thread
    handler.uninstall()
    assert sys.excepthook is foreign_sys
    assert threading.excepthook is foreign_thread
    assert handler.installed is False


def test_uncaught_main_thread_exception_is_logged_critical(list_logger) -> None:
    handler = UncaughtExceptionHandler(list_logger)
    try:
        raise ValueError("kaput")
    except ValueError:
        exc_info = sys.exc_info()
    handler._on_uncaught(*exc_info)

    (record,) = list_logger.handlers[0].records
    assert record.levelno == logging.CRITICAL
    assert record.getMessage() == "Uncaught exception"
    assert record.exc_info[1] is exc_info[1]


def test_keyboard_interrupt_is_delegated_to_previous_hook(list_logger) -> None:
    calls: list[tuple] = []
    sys.excepthook = lambda *args: calls.append(args)
    handler = UncaughtExceptionHandler(list_logger)
    handler.install()

    handler._on_uncaught(KeyboardInterrupt, KeyboardInterrupt(), None)
    assert len(calls) == 1 and calls[0][0] is KeyboardInterrupt
    assert list_logger.handlers[0].records == []


def test_uncaught_thread_exception_is_logged_with_thread_name(list_logger) -> None:
    handler = UncaughtExceptionHandler(list_logger)
    thread = threading.Thread(name="worker-7")
    error = RuntimeError("thread boom")
    handler._on_thread_uncaught(threading.ExceptHookArgs((RuntimeError, error, None, thread)))

    (record,) = list_logger.handlers[0].records
    assert record.levelno == logging.CRITICAL
    assert record.getMessage() == "Uncaught exception in thread worker-7"
    assert record.exc_info[1] is error


def test_uncaught_thread_exception_without_thread_is_logged_as_unknown(list_logger) -> None:
    handler = UncaughtExceptionHandler(list_logger)
    handler._on_thread_uncaught(threading.ExceptHookArgs((ValueError, ValueError("x"), None, None)))
    assert list_logger.handlers[0].records[0].getMessage() == "Uncaught exception in thread unknown"


def test_system_exit_in_a_thread_is_ignored(list_logger) -> None:
    handler = UncaughtExceptionHandler(list_logger)
    handler._on_thread_uncaught(threading.ExceptHookArgs((SystemExit, SystemExit(0), None, threading.current_thread())))
    assert list_logger.handlers[0].records == []


def test_real_thread_crash_is_captured(list_logger) -> None:
    handler = UncaughtExceptionHandler(list_logger)
    handler.install()

    def crash() -> None:
        raise ValueError("really crashed")

    thread = threading.Thread(target=crash, name="crasher")
    thread.start()
    thread.join()
    handler.uninstall()

    (record,) = list_logger.handlers[0].records
    assert "crasher" in record.getMessage()
    assert str(record.exc_info[1]) == "really crashed"


# --- LogManager ------------------------------------------------------------------


def test_get_logger() -> None:
    assert LogManager.get_logger() is logging.getLogger()
    assert LogManager.get_logger("pycrux.x") is logging.getLogger("pycrux.x")


def test_configure_installs_handlers_and_returns_logger() -> None:
    logger = LogManager.configure({"level": "debug", "outputs": [{}, {"stream": "stdout"}]})
    assert logger is logging.getLogger()
    assert logger.level == logging.DEBUG
    assert len(LogManager._handlers) == 2
    assert all(h in logger.handlers for h in LogManager._handlers)


def test_configure_twice_replaces_previous_handlers() -> None:
    logger = LogManager.configure({"outputs": [{}, {}]})
    first = list(LogManager._handlers)
    LogManager.configure({"outputs": [{}]})
    assert len(LogManager._handlers) == 1
    assert not any(h in logger.handlers for h in first)


def test_configure_accepts_log_config_and_none() -> None:
    assert LogManager.configure(LogConfig(level=logging.ERROR)).level == logging.ERROR
    assert LogManager.configure(None).level == logging.INFO


def test_configure_scoped_logger_leaves_root_untouched() -> None:
    root_handlers = list(logging.getLogger().handlers)
    logger = LogManager.configure({"level": "warn"}, name="pycrux.scoped")
    assert logger.name == "pycrux.scoped"
    assert logger.level == logging.WARNING
    assert logging.getLogger().handlers == root_handlers
    LogManager.shutdown()
    assert LogManager._handlers[:] == []
    assert logger.handlers == []


def test_per_logger_levels_are_applied_and_restored() -> None:
    noisy = logging.getLogger("pycrux.noisy")
    noisy.setLevel(logging.DEBUG)
    LogManager.configure({"levels": {"pycrux.noisy": "error"}})
    assert noisy.level == logging.ERROR
    LogManager.shutdown()
    assert noisy.level == logging.DEBUG


def test_shutdown_restores_root_level_and_is_idempotent() -> None:
    root = logging.getLogger()
    original = root.level
    LogManager.configure({"level": "critical"})
    assert root.level == logging.CRITICAL
    LogManager.shutdown()
    LogManager.shutdown()
    assert root.level == original


def test_capture_uncaught_installs_and_shutdown_uninstalls() -> None:
    before = sys.excepthook
    LogManager.configure({"capture_uncaught": True})
    assert LogManager._uncaught is not None and LogManager._uncaught.installed
    assert sys.excepthook is not before
    LogManager.shutdown()
    assert LogManager._uncaught is None
    assert sys.excepthook is before


def test_env_overrides_are_applied(tmp_path) -> None:
    path = tmp_path / "env.json"
    LogManager.configure(
        {"outputs": [{}]},
        name="pycrux.env",
        env={"PYCRUX_LOG_LEVEL": "debug", "PYCRUX_LOG_FILE": str(path), "PYCRUX_LOG_FORMAT": "json"},
    )
    logger = logging.getLogger("pycrux.env")
    assert logger.level == logging.DEBUG
    logger.info("hello env")
    LogManager.shutdown()
    assert json.loads(path.read_text(encoding="utf-8").splitlines()[0])["message"] == "hello env"


def test_logging_end_to_end_with_mdc_and_defaults(tmp_path) -> None:
    path = tmp_path / "e2e"
    LogManager.configure(
        {
            "outputs": [{"format": "json", "path": str(path)}],
            "mdc_defaults": {"app": "svc"},
        },
        name="pycrux.e2e",
    )
    with MDC.request_scope("req-9", userId="42"):
        logging.getLogger("pycrux.e2e").info("order %s created", 5)
    LogManager.shutdown()

    data = json.loads((tmp_path / "e2e.json").read_text(encoding="utf-8").splitlines()[0])
    assert data["message"] == "order 5 created"
    assert data["mdc"] == {"app": "svc", "requestId": "req-9", "userId": "42"}
