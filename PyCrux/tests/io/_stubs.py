"""Minimal stand-ins for the third-party packages that ``pycrux.io.base`` / ``buffers`` / ``symbols`` import.

``solidlsp``, ``serena``, ``sensai`` and ``pathspec`` are not declared dependencies of PyCrux, so they are
usually missing in the test environment. :func:`install` registers tiny replacements in ``sys.modules`` —
only for packages that are really absent — implementing just the surface those modules use. The unit tests
then exercise PyCrux's own logic against a fake language-server process instead of a real one.

``STUBBED`` lists the packages that were replaced; tests that depend on the exact stub behaviour call
``require_stubs()`` and are skipped when the real packages are installed.
"""

from __future__ import annotations

import dataclasses
import enum
import importlib.util
import os
import pickle
import sys
import types
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import pytest

STUBBED: set[str] = set()


def require_stubs() -> None:
    """Skip the calling module when the real third-party packages are installed."""
    if not {"solidlsp", "serena", "sensai", "pathspec"} <= STUBBED:
        pytest.skip("real solidlsp/serena/sensai/pathspec packages are installed", allow_module_level=True)


# --- helpers ------------------------------------------------------------------------------


def _register(name: str, *, package: bool = False, **attrs: Any) -> types.ModuleType:
    module = types.ModuleType(name)
    if package:
        module.__path__ = []  # type: ignore[attr-defined]
    module.__dict__.update(attrs)
    sys.modules[name] = module
    parent, _, child = name.rpartition(".")
    if parent:
        setattr(sys.modules[parent], child, module)
    return module


def _dict_types(module: types.ModuleType) -> None:
    """Make ``module.Anything`` a ``dict`` subclass created on first access (TypedDict-like constructors)."""

    def __getattr__(name: str) -> type:
        if name.startswith("__"):
            raise AttributeError(name)
        # ``__module__`` makes the class picklable by reference (the symbol caches are pickled)
        cls = type(name, (dict,), {"__module__": module.__name__})
        setattr(module, name, cls)
        return cls

    module.__getattr__ = __getattr__  # type: ignore[attr-defined]


def _missing(top_level: str) -> bool:
    return importlib.util.find_spec(top_level) is None


# --- pathspec ---------------------------------------------------------------------------------


class _PathSpec:
    def __init__(self, patterns: list[str]) -> None:
        self.patterns = patterns

    @classmethod
    def from_lines(cls, _pattern_factory: Any, lines: Any) -> "_PathSpec":
        return cls([line.strip() for line in lines if line.strip() and not line.startswith("#")])

    def match_file(self, path: str) -> bool:
        path = str(path).replace("\\", "/")
        for raw in self.patterns:
            pattern = raw.rstrip("/")
            if fnmatch(path, pattern) or fnmatch(path, pattern + "/*"):
                return True
            if any(fnmatch(part, pattern) for part in path.split("/")):
                return True
        return False


def _install_pathspec() -> None:
    _register("pathspec", package=True, PathSpec=_PathSpec)
    _register("pathspec.patterns", GitWildMatchPattern=type("GitWildMatchPattern", (), {}))


# --- sensai ------------------------------------------------------------------------------------


def _install_sensai() -> None:
    def getstate(_cls: type, obj: Any, transient_properties: list[str] | None = None, **_kw: Any) -> dict:
        # like sensai: transient properties are reset to None in the pickled state
        transient = set(transient_properties or [])
        return {k: (None if k in transient else v) for k, v in obj.__dict__.items()}

    def load_pickle(path: str | os.PathLike[str]) -> Any:
        with open(path, "rb") as handle:
            return pickle.load(handle)

    _register("sensai", package=True)
    _register("sensai.util", package=True)
    _register("sensai.util.pickle", getstate=getstate, load_pickle=load_pickle)
    _register("sensai.util.string", ToStringMixin=type("ToStringMixin", (), {}))


# --- serena --------------------------------------------------------------------------------------


@dataclasses.dataclass
class _MatchedConsecutiveLines:
    contents: str
    line: int
    context_lines_before: int
    context_lines_after: int
    source_file_path: str | None

    @classmethod
    def from_file_contents(
        cls,
        file_contents: str,
        line: int,
        context_lines_before: int = 0,
        context_lines_after: int = 0,
        source_file_path: str | None = None,
    ) -> "_MatchedConsecutiveLines":
        return cls(file_contents, line, context_lines_before, context_lines_after, source_file_path)


def _install_serena() -> None:
    def match_path(relative_path: str, path_spec: Any, root_path: str | None = None) -> bool:
        return bool(path_spec.match_file(relative_path))

    _register("serena", package=True)
    _register("serena.util", package=True)
    _register("serena.util.file_system", match_path=match_path)
    _register("serena.util.text_utils", MatchedConsecutiveLines=_MatchedConsecutiveLines)


# --- solidlsp --------------------------------------------------------------------------------------


class SolidLSPException(Exception):
    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class LSPError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclasses.dataclass
class ProcessLaunchInfo:
    cmd: Any = None
    cwd: str | None = None
    env: dict[str, str] | None = None


class SymbolKind(enum.IntEnum):
    File = 1
    Module = 2
    Namespace = 3
    Package = 4
    Class = 5
    Method = 6
    Property = 7
    Field = 8
    Constructor = 9
    Enum = 10
    Interface = 11
    Function = 12
    Variable = 13
    Constant = 14


class CompletionItemKind(enum.IntEnum):
    Text = 1
    Method = 2
    Function = 3
    Keyword = 14


class CompletionTriggerKind(enum.IntEnum):
    Invoked = 1


class LSPConstants:
    TEXT_DOCUMENT = "textDocument"
    VERSION = "version"
    URI = "uri"
    CONTENT_CHANGES = "contentChanges"
    RANGE = "range"
    POSITION = "position"
    LINE = "line"
    CHARACTER = "character"
    TARGET_URI = "targetUri"
    TARGET_RANGE = "targetRange"
    TARGET_SELECTION_RANGE = "targetSelectionRange"
    NAME = "name"
    KIND = "kind"
    LOCATION = "location"
    LANGUAGE_ID = "languageId"
    TEXT = "text"


class FilenameMatcher:
    def __init__(self, *patterns: str) -> None:
        self.patterns = patterns

    def is_relevant_filename(self, filename: str) -> bool:
        return any(fnmatch(os.path.basename(filename), pattern) for pattern in self.patterns)


class Language:
    """Stand-in for ``solidlsp.ls_config.Language`` (everything is "python")."""

    ls_class: type | None = None

    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"Language({self.value!r})"

    @classmethod
    def from_ls_class(cls, _ls_class: type) -> "Language":
        return cls("python")

    def get_ls_class(self) -> type:
        assert Language.ls_class is not None, "tests must set Language.ls_class"
        return Language.ls_class

    def get_source_fn_matcher(self) -> FilenameMatcher:
        return FilenameMatcher("*.py")


@dataclasses.dataclass
class LanguageServerConfig:
    code_language: Language = dataclasses.field(default_factory=lambda: Language("python"))
    ignored_paths: list[str] = dataclasses.field(default_factory=list)
    encoding: str = "utf-8"
    trace_lsp_communication: bool = False
    start_independent_lsp_process: bool = False


class LanguageServerProcess:
    def __init__(
        self,
        launch_info: Any,
        language: Any = None,
        determine_log_level: Any = None,
        logger: Any = None,
        start_independent_lsp_process: bool = False,
    ) -> None:
        self.launch_info = launch_info
        self.language = language
        self.determine_log_level = determine_log_level
        self.logger = logger
        self.start_independent_lsp_process = start_independent_lsp_process
        self.timeout: float | None = None
        self.process: Any = None
        self.running = False
        self.send = types.SimpleNamespace()
        self.notify = types.SimpleNamespace()

    def set_request_timeout(self, timeout: float | None) -> None:
        self.timeout = timeout

    def is_running(self) -> bool:
        return self.running

    def shutdown(self) -> None:
        self.running = False


class SolidLSPSettings:
    class CustomLSSettings(dict):
        pass

    def __init__(self, ls_resources_dir: str = "", project_data_path: str = "", ls_specific: dict | None = None) -> None:
        self.ls_resources_dir = ls_resources_dir
        self.project_data_path = project_data_path
        self._ls_specific = ls_specific or {}

    def get_ls_specific_settings(self, _language: Any) -> "SolidLSPSettings.CustomLSSettings":
        return SolidLSPSettings.CustomLSSettings(self._ls_specific)


def _save_cache(file: str, version: Any, data: Any) -> None:
    with open(file, "wb") as handle:
        pickle.dump((version, data), handle)


def _load_cache(file: str, version: Any) -> Any:
    with open(file, "rb") as handle:
        saved_version, data = pickle.load(handle)
    return data if saved_version == version else None


def _install_solidlsp() -> None:
    _register("solidlsp", package=True)
    ls_types = _register("solidlsp.ls_types", SymbolKind=SymbolKind)
    _dict_types(ls_types)
    _register("solidlsp.ls_exceptions", SolidLSPException=SolidLSPException)
    _register(
        "solidlsp.ls_config",
        FilenameMatcher=FilenameMatcher,
        Language=Language,
        LanguageServerConfig=LanguageServerConfig,
    )
    _register("solidlsp.ls_process", LanguageServerProcess=LanguageServerProcess)
    _register("solidlsp.settings", SolidLSPSettings=SolidLSPSettings)
    _register("solidlsp.util", package=True)
    _register("solidlsp.util.cache", load_cache=_load_cache, save_cache=_save_cache)
    _register("solidlsp.lsp_protocol_handler", package=True)
    lsp_types = _register(
        "solidlsp.lsp_protocol_handler.lsp_types",
        CompletionItemKind=CompletionItemKind,
        CompletionTriggerKind=CompletionTriggerKind,
    )
    _dict_types(lsp_types)
    _register("solidlsp.lsp_protocol_handler.lsp_constants", LSPConstants=LSPConstants)
    _register(
        "solidlsp.lsp_protocol_handler.server",
        LSPError=LSPError,
        ProcessLaunchInfo=ProcessLaunchInfo,
        StringDict=dict,
    )


def install() -> None:
    """Register the stand-ins for every missing third-party package (idempotent)."""
    installers = {
        "pathspec": _install_pathspec,
        "sensai": _install_sensai,
        "serena": _install_serena,
        "solidlsp": _install_solidlsp,
    }
    for name, installer in installers.items():
        if name not in STUBBED and _missing(name):
            installer()
            STUBBED.add(name)


__all__ = ["STUBBED", "install", "require_stubs", "Path"]
