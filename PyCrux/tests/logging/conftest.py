"""Shared fixtures for the logging tests: keep global logging state isolated between tests."""

import logging
import sys
import threading

import pytest

from pycrux.logging import MDC, LogManager


@pytest.fixture(autouse=True)
def _isolate_logging_state():
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    sys_hook, thread_hook = sys.excepthook, threading.excepthook
    MDC.clear()
    try:
        yield
    finally:
        LogManager.shutdown()
        MDC.clear()
        root.handlers[:] = handlers
        root.setLevel(level)
        sys.excepthook, threading.excepthook = sys_hook, thread_hook


class ListHandler(logging.Handler):
    """Collects emitted records."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture
def list_logger():
    """A non-propagating logger that stores its records in ``logger.handlers[0].records``."""
    logger = logging.getLogger("pycrux.tests.list_logger")
    handler = ListHandler()
    logger.handlers[:] = [handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    yield logger
    logger.handlers[:] = []
    logger.propagate = True


def make_record(
    message: str = "hello",
    *,
    level: int = logging.INFO,
    name: str = "pycrux.tests",
    args: tuple = (),
    exc_info=None,
    func: str = "test_func",
) -> logging.LogRecord:
    """Build a ``LogRecord`` with deterministic location fields."""
    return logging.LogRecord(name, level, "/tmp/sample.py", 42, message, args, exc_info, func)
