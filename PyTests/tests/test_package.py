"""Smoke tests for the installable pytests package."""

import pytests
from pytests.helpers import assert_exception


def test_version():
    assert pytests.__version__


def test_assert_exception_helper():
    with assert_exception(ValueError):
        raise ValueError("expected")
