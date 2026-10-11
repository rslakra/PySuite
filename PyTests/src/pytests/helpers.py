"""Reusable helpers for pytest modules across PySuite projects."""

import contextlib

__all__ = ["assert_exception"]


@contextlib.contextmanager
def assert_exception(exc_type):
    """Assert that a block raises ``exc_type``."""
    try:
        yield
    except exc_type:
        return
    else:
        raise AssertionError(f"No {exc_type.__name__} was raised.")
