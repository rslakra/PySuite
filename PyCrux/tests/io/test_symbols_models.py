"""Tests for the symbol model classes in ``pycrux.io.symbols`` (no language server involved)."""

import dataclasses
import pickle
from types import SimpleNamespace

import pytest

import pycrux.io.symbols as symbols
from pycrux.io.symbols import (
    DocumentSymbols,
    LanguageServerDependencyProvider,
    LanguageServerDependencyProviderSinglePath,
    ReferenceInSymbol,
    SymbolBody,
    SymbolBodyFactory,
)

from . import _stubs
from ._fakes import SOURCE_LINES, rng

_stubs.require_stubs()

SOLID_SETTINGS = symbols.SolidLSPSettings.CustomLSSettings


# --- ReferenceInSymbol -----------------------------------------------------------------------------


def test_reference_in_symbol_is_a_keyword_only_dataclass() -> None:
    assert dataclasses.is_dataclass(ReferenceInSymbol)
    ref = ReferenceInSymbol(symbol={"name": "f"}, line=3, character=4)
    assert (ref.symbol, ref.line, ref.character) == ({"name": "f"}, 3, 4)
    with pytest.raises(TypeError):
        ReferenceInSymbol({"name": "f"}, 3, 4)  # type: ignore[misc]


# --- SymbolBody --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        ((0, 0, 2, 16), None, "class Foo:\n    def bar(self):\n        return 1"),  # whole class
        ((1, 4, 2, 16), None, "def bar(self):\n        return 1"),  # leading indentation removed
        ((1, 8, 1, 11), None, "bar"),  # single line, both ends trimmed
        ((0, 6, 0, 9), None, "Foo"),
        ((8, 0, 8, 12), None, "x = helper()"),
        ((5, 4, 5, 7), None, "foo"),
        ((4, 0, 5, 7), None, "def helper():\n    foo"),  # last line cut short
        ((0, 0, 0, 0), None, ""),  # empty range
    ],
)
def test_symbol_body_get_text(start: tuple, end, expected: str) -> None:
    assert SymbolBody(SOURCE_LINES, *start).get_text() == expected


def test_symbol_body_shares_the_lines_buffer() -> None:
    body = SymbolBody(SOURCE_LINES, 0, 0, 0, 10)
    assert body._lines is SOURCE_LINES
    assert body._tostring_excludes() == ["_lines"]


def test_symbol_body_text_reflects_the_buffer_at_call_time() -> None:
    lines = ["abc", "def"]
    body = SymbolBody(lines, 0, 1, 1, 2)
    assert body.get_text() == "bc\nde"
    lines[1] = "xyz"
    assert body.get_text() == "bc\nxy"


# --- SymbolBodyFactory -------------------------------------------------------------------------------


def _file_buffer() -> SimpleNamespace:
    return SimpleNamespace(split_lines=lambda: SOURCE_LINES)


def _symbol(location_range: dict, **extra) -> dict:
    return {"name": "s", "location": {"range": location_range}, **extra}


def test_factory_creates_a_body_from_the_symbol_location() -> None:
    factory = SymbolBodyFactory(_file_buffer())
    body = factory.create_symbol_body(_symbol(rng(1, 4, 2, 16)))
    assert isinstance(body, SymbolBody)
    assert body.get_text() == "def bar(self):\n        return 1"


def test_factory_bodies_share_one_lines_buffer() -> None:
    factory = SymbolBodyFactory(_file_buffer())
    first = factory.create_symbol_body(_symbol(rng(0, 0, 0, 10)))
    second = factory.create_symbol_body(_symbol(rng(4, 0, 4, 13)))
    assert first._lines is second._lines is SOURCE_LINES


def test_factory_returns_an_existing_body_unchanged() -> None:
    factory = SymbolBodyFactory(_file_buffer())
    existing = SymbolBody(["x"], 0, 0, 0, 1)
    assert factory.create_symbol_body(_symbol(rng(0, 0, 0, 10), body=existing)) is existing


def test_factory_replaces_a_body_that_is_not_a_symbol_body() -> None:
    factory = SymbolBodyFactory(_file_buffer())
    body = factory.create_symbol_body(_symbol(rng(0, 6, 0, 9), body="stale text"))
    assert isinstance(body, SymbolBody) and body.get_text() == "Foo"


def test_factory_requires_a_location() -> None:
    with pytest.raises(AssertionError):
        SymbolBodyFactory(_file_buffer()).create_symbol_body({"name": "no-location"})  # type: ignore[arg-type]


# --- DocumentSymbols ----------------------------------------------------------------------------------


def _tree() -> list[dict]:
    return [
        {"name": "A", "children": [{"name": "A1", "children": [{"name": "A1a"}]}, {"name": "A2"}]},
        {"name": "B", "children": []},
    ]


def test_iter_symbols_is_depth_first() -> None:
    assert [s["name"] for s in DocumentSymbols(_tree()).iter_symbols()] == ["A", "A1", "A1a", "A2", "B"]


def test_iter_symbols_of_an_empty_document() -> None:
    assert list(DocumentSymbols([]).iter_symbols()) == []


def test_get_all_symbols_and_roots() -> None:
    roots = _tree()
    document = DocumentSymbols(roots)
    all_symbols, returned_roots = document.get_all_symbols_and_roots()
    assert [s["name"] for s in all_symbols] == ["A", "A1", "A1a", "A2", "B"]
    assert returned_roots is roots


def test_get_all_symbols_is_computed_once_and_reused_by_iter_symbols() -> None:
    document = DocumentSymbols(_tree())
    first, _ = document.get_all_symbols_and_roots()
    second, _ = document.get_all_symbols_and_roots()
    assert first is second
    assert list(document.iter_symbols()) == first


def test_pickling_drops_the_derived_symbol_list() -> None:
    document = DocumentSymbols(_tree())
    document.get_all_symbols_and_roots()
    state = document.__getstate__()
    assert state["_all_symbols"] is None
    assert state["root_symbols"] == document.root_symbols

    restored = pickle.loads(pickle.dumps(document))
    assert restored._all_symbols is None
    assert [s["name"] for s in restored.iter_symbols()] == ["A", "A1", "A1a", "A2", "B"]


# --- dependency providers ---------------------------------------------------------------------------------


class RecordingProvider(LanguageServerDependencyProvider):
    def create_launch_command(self) -> list[str]:
        return ["recorded", self._ls_resources_dir]


def test_dependency_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        LanguageServerDependencyProvider(SOLID_SETTINGS(), "/res")  # type: ignore[abstract]


def test_dependency_provider_keeps_settings_and_resource_dir() -> None:
    settings = SOLID_SETTINGS({"ls_path": "/x"})
    provider = RecordingProvider(settings, "/res")
    assert provider._custom_settings is settings
    assert provider._ls_resources_dir == "/res"
    assert provider.create_launch_command() == ["recorded", "/res"]


def test_dependency_provider_default_environment_is_empty() -> None:
    assert RecordingProvider(SOLID_SETTINGS(), "/res").create_launch_command_env() == {}


def test_dependency_provider_environment_can_be_overridden() -> None:
    class WithEnv(RecordingProvider):
        def create_launch_command_env(self) -> dict[str, str]:
            return {"JAVA_HOME": "/jdk"}

    assert WithEnv(SOLID_SETTINGS(), "/res").create_launch_command_env() == {"JAVA_HOME": "/jdk"}


class SinglePathProvider(LanguageServerDependencyProviderSinglePath):
    installed = 0

    def _get_or_install_core_dependency(self) -> str:
        type(self).installed += 1
        return "/installed/server"

    def _create_launch_command(self, core_path: str) -> list[str]:
        return [core_path, "--stdio"]


def test_single_path_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        LanguageServerDependencyProviderSinglePath(SOLID_SETTINGS(), "/res")  # type: ignore[abstract]


def test_single_path_provider_installs_when_no_path_is_configured() -> None:
    SinglePathProvider.installed = 0
    provider = SinglePathProvider(SOLID_SETTINGS(), "/res")
    assert provider.create_launch_command() == ["/installed/server", "--stdio"]
    assert SinglePathProvider.installed == 1


def test_single_path_provider_prefers_the_user_configured_path() -> None:
    SinglePathProvider.installed = 0
    provider = SinglePathProvider(SOLID_SETTINGS({"ls_path": "/custom/server"}), "/res")
    assert provider.create_launch_command() == ["/custom/server", "--stdio"]
    assert SinglePathProvider.installed == 0


# --- module-level definitions ---------------------------------------------------------------------------------


def test_raw_document_symbol_alias_is_a_union_of_both_lsp_shapes() -> None:
    assert symbols.RawDocumentSymbol is not None
    assert symbols.log.name == "pycrux.io.symbols"
