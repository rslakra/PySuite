"""Shared test helpers."""

import importlib
import sys
import warnings
from types import ModuleType

import pytest


def pytest_unconfigure(config) -> None:
    """Silence the interpreter-shutdown form of the PyMuPDF (SWIG) deprecation warning.

    ``pyproject.toml`` filters it while the tests run, but the same warning is printed again when the
    interpreter exits, after pytest has restored the warning filters. Adding the filter here, at the very end
    of the session, keeps it active for that last message.
    """
    warnings.filterwarnings("ignore", message=r"builtin type .* has no __module__ attribute", category=DeprecationWarning)


@pytest.fixture
def reload_without(monkeypatch):
    """Reload a module while the given third-party packages are "not installed".

    ``sys.modules[name] = None`` makes ``import name`` raise ``ImportError``, which exercises the
    guarded ``try / except ImportError`` blocks at the top of the optional-dependency modules. The
    reloaded modules are reloaded again (with the real packages) when the test ends.
    """
    reloaded: list[ModuleType] = []

    def apply(module: ModuleType, *missing: str) -> ModuleType:
        for name in missing:
            monkeypatch.setitem(sys.modules, name, None)
        reloaded.append(module)
        return importlib.reload(module)

    yield apply

    monkeypatch.undo()
    for module in reversed(reloaded):
        importlib.reload(module)
