"""Tests for ``pycrux.net`` — the ``HttpUtils`` placeholder and the (still empty) ``net.http`` package."""

import importlib

import pytest

import pycrux.net as net_package
from pycrux.net import HttpUtils
from pycrux.net.http_utils import HttpUtils as HttpUtilsFromModule


def test_http_utils_is_exported_from_the_package() -> None:
    assert HttpUtils is HttpUtilsFromModule
    assert net_package.__all__ == ["HttpUtils"]


def test_http_utils_can_be_instantiated() -> None:
    assert isinstance(HttpUtils(), HttpUtils)


@pytest.mark.parametrize("module", ["body", "client", "headers", "message", "request", "response", "server", "status"])
def test_http_submodules_are_importable(module: str) -> None:
    assert importlib.import_module(f"pycrux.net.http.{module}").__name__ == f"pycrux.net.http.{module}"
