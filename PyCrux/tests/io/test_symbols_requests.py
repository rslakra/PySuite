"""Tests for the LSP request methods of ``SolidLanguageServer`` (definition, references, completion, hover, ...)."""

import logging

import pytest

import pycrux.io.symbols as symbols
from solidlsp.lsp_protocol_handler.server import LSPError

from . import _stubs
from ._fakes import SOURCE, rng, write_files

_stubs.require_stubs()

SolidLSPException = symbols.SolidLSPException


@pytest.fixture
def sleeps(monkeypatch) -> list[float]:
    """Replace ``time.sleep`` used for the cross-file wait so the tests stay fast."""
    calls: list[float] = []
    monkeypatch.setattr(symbols, "sleep", calls.append)
    return calls


@pytest.fixture
def ls(make_ls, sleeps):
    return make_ls({"mod.py": SOURCE, "other.py": SOURCE})


def location(ls, rel: str, *positions: int) -> dict:
    return {"uri": (ls.repo / rel).as_uri(), "range": rng(*positions)}


def expected(ls, rel: str, *positions: int) -> dict:
    return {
        "uri": (ls.repo / rel).as_uri(),
        "range": rng(*positions),
        "absolutePath": str(ls.repo / rel),
        "relativePath": rel,
    }


# --- _create_text_document_position_params ---------------------------------------------------------------------


def test_position_params(ls) -> None:
    assert ls._create_text_document_position_params("mod.py", 3, 5) == {
        "textDocument": {"uri": (ls.repo / "mod.py").as_uri()},
        "position": {"line": 3, "character": 5},
    }


# --- request_definition -----------------------------------------------------------------------------------------


def test_request_definition_converts_a_location_list(ls) -> None:
    ls.server.send.respond("definition", [location(ls, "mod.py", 4, 4, 4, 10), location(ls, "other.py", 0, 6, 0, 9)])

    result = ls.request_definition("mod.py", 7, 15)

    assert result == [expected(ls, "mod.py", 4, 4, 4, 10), expected(ls, "other.py", 0, 6, 0, 9)]
    assert ls.server.send.requests == [
        ("definition", {"textDocument": {"uri": (ls.repo / "mod.py").as_uri()}, "position": {"line": 7, "character": 15}})
    ]


def test_request_definition_accepts_a_single_location(ls) -> None:
    ls.server.send.respond("definition", location(ls, "mod.py", 4, 4, 4, 10))
    assert ls.request_definition("mod.py", 7, 15) == [expected(ls, "mod.py", 4, 4, 4, 10)]


def test_request_definition_accepts_location_links(ls) -> None:
    link = {
        "targetUri": (ls.repo / "mod.py").as_uri(),
        "targetRange": rng(4, 0, 7, 20),
        "targetSelectionRange": rng(4, 4, 4, 10),
    }
    ls.server.send.respond("definition", [link])
    assert ls.request_definition("mod.py", 7, 15) == [expected(ls, "mod.py", 4, 4, 4, 10)]


def test_request_definition_without_result(ls, caplog) -> None:
    ls.server.send.respond("definition", None)
    with caplog.at_level(logging.WARNING, logger="pycrux.io.symbols"):
        assert ls.request_definition("mod.py", 1, 1) == []
    assert "returned None for request_definition request at mod.py:1:1" in caplog.text
    ls.server.send.respond("definition", [])
    assert ls.request_definition("mod.py", 1, 1) == []


def test_request_definition_requires_a_started_server(make_ls) -> None:
    ls = make_ls({"mod.py": SOURCE}, started=False)
    with pytest.raises(SolidLSPException, match="Language Server not started"):
        ls.request_definition("mod.py", 0, 0)


def test_request_definition_skips_locations_outside_the_repository(ls, monkeypatch, caplog) -> None:
    ls.server.send.respond("definition", [location(ls, "mod.py", 4, 4, 4, 10)])
    monkeypatch.setattr(symbols.PathUtils, "get_relative_path", staticmethod(lambda path, base: None))
    with caplog.at_level(logging.WARNING, logger="pycrux.io.symbols"):
        assert ls.request_definition("mod.py", 7, 15) == []
    assert "outside the repository" in caplog.text


def test_request_definition_skips_ignored_paths(make_ls, sleeps, caplog) -> None:
    ls = make_ls({"mod.py": SOURCE, ".hidden/x.py": SOURCE, "notes.txt": "t"})
    ls.server.send.respond(
        "definition",
        [location(ls, ".hidden/x.py", 0, 0, 0, 1), location(ls, "notes.txt", 0, 0, 0, 1), location(ls, "mod.py", 0, 0, 0, 1)],
    )
    with caplog.at_level(logging.INFO, logger="pycrux.io.symbols"):
        result = ls.request_definition("mod.py", 1, 1)
    assert [item["relativePath"] for item in result] == ["mod.py"]
    assert caplog.text.count("found symbol in ignored path") == 2


@pytest.mark.parametrize(
    "response",
    ["a string", 42, [None], ["not a dict"], [{"unexpected": "shape"}], {"uri": "file:///x"}],
)
def test_request_definition_rejects_unexpected_responses(ls, response) -> None:
    ls.server.send.respond("definition", response)
    with pytest.raises(AssertionError):
        ls.request_definition("mod.py", 1, 1)


def test_internal_lsp_errors_are_reported_helpfully(ls) -> None:
    ls.server.send.respond("definition", LSPError(-32603, "internal"))
    with pytest.raises(RuntimeError, match=r"LSP internal error \(-32603\) when requesting request_definition for mod.py:3:4") as info:
        ls.request_definition("mod.py", 3, 4)
    assert isinstance(info.value.__cause__, LSPError)


@pytest.mark.parametrize("error", [LSPError(-32000, "other"), ValueError("bad"), KeyError("k")])
def test_other_errors_are_re_raised_unchanged(ls, error) -> None:
    ls.server.send.respond("definition", error)
    with pytest.raises(type(error)):
        ls.request_definition("mod.py", 1, 1)


def test_requests_open_and_close_the_file(ls) -> None:
    ls.server.send.respond("definition", [])
    ls.request_definition("mod.py", 1, 1)
    assert len(ls.server.notify.of("open")) == 1 and len(ls.server.notify.of("close")) == 1
    assert ls.open_file_buffers == {}


def test_the_file_is_closed_when_a_request_fails(ls) -> None:
    ls.server.send.respond("definition", ValueError("bad"))
    with pytest.raises(ValueError):
        ls.request_definition("mod.py", 1, 1)
    assert ls.open_file_buffers == {}


# --- cross-file wait --------------------------------------------------------------------------------------------------


def test_cross_file_wait_happens_once(ls, sleeps) -> None:
    ls.server.send.respond("definition", [])
    ls.request_definition("mod.py", 1, 1)
    ls.request_definition("mod.py", 2, 2)
    assert sleeps == [2]
    assert ls._has_waited_for_cross_file_references is True


def test_cross_file_wait_uses_the_overridable_duration(make_ls, sleeps) -> None:
    ls = make_ls({"mod.py": SOURCE})
    ls._get_wait_time_for_cross_file_referencing = lambda: 0.25
    ls._wait_for_cross_file_references_if_needed()
    ls._wait_for_cross_file_references_if_needed()
    assert sleeps == [0.25]


# --- request_implementation ---------------------------------------------------------------------------------------------


def test_request_implementation(ls) -> None:
    ls.server.send.respond("implementation", [location(ls, "other.py", 1, 8, 1, 11)])
    assert ls.request_implementation("mod.py", 1, 8) == [expected(ls, "other.py", 1, 8, 1, 11)]
    assert ls.server.send.requests[0][0] == "implementation"


def test_request_implementation_without_result(ls, caplog) -> None:
    ls.server.send.respond("implementation", None)
    with caplog.at_level(logging.WARNING, logger="pycrux.io.symbols"):
        assert ls.request_implementation("mod.py", 1, 8) == []
    assert "request_implementation" in caplog.text


def test_request_implementation_requires_a_started_server(make_ls, caplog) -> None:
    ls = make_ls({"mod.py": SOURCE}, started=False)
    with caplog.at_level(logging.ERROR, logger="pycrux.io.symbols"):
        with pytest.raises(SolidLSPException):
            ls.request_implementation("mod.py", 0, 0)
    assert "request_implementation called before language server started" in caplog.text


def test_implementation_errors_mention_the_request_name(ls) -> None:
    ls.server.send.respond("implementation", LSPError(-32603, "internal"))
    with pytest.raises(RuntimeError, match="requesting request_implementation"):
        ls.request_implementation("mod.py", 1, 1)


# --- request_references --------------------------------------------------------------------------------------------------


def test_request_references_sends_the_expected_request(ls) -> None:
    ls.server.send.respond("references", [location(ls, "mod.py", 5, 10, 5, 13)])

    assert ls.request_references("mod.py", 0, 6) == [expected(ls, "mod.py", 5, 10, 5, 13)]
    assert ls.server.send.requests == [
        (
            "references",
            {
                "textDocument": {"uri": (ls.repo / "mod.py").as_uri()},
                "position": {"line": 0, "character": 6},
                "context": {"includeDeclaration": False},
            },
        )
    ]


def test_request_references_without_result(ls) -> None:
    ls.server.send.respond("references", None)
    assert ls.request_references("mod.py", 0, 6) == []
    ls.server.send.respond("references", [])
    assert ls.request_references("mod.py", 0, 6) == []


def test_request_references_filters_ignored_files(make_ls, sleeps) -> None:
    ls = make_ls({"mod.py": SOURCE, ".hidden/x.py": SOURCE})
    ls.server.send.respond("references", [location(ls, ".hidden/x.py", 0, 0, 0, 1), location(ls, "mod.py", 5, 10, 5, 13)])
    assert [r["relativePath"] for r in ls.request_references("mod.py", 0, 6)] == ["mod.py"]


@pytest.mark.parametrize("response", ["text", {"uri": "x"}, [1], ["s"], [{"bad": "shape"}]])
def test_request_references_rejects_unexpected_responses(ls, response) -> None:
    ls.server.send.respond("references", response)
    with pytest.raises(AssertionError):
        ls.request_references("mod.py", 0, 6)


def test_request_references_requires_a_started_server(make_ls) -> None:
    ls = make_ls({"mod.py": SOURCE}, started=False)
    with pytest.raises(SolidLSPException):
        ls.request_references("mod.py", 0, 0)


def test_request_references_logs_performance_when_debugging(ls, monkeypatch, caplog) -> None:
    monkeypatch.setattr(symbols, "_debug_enabled", True)
    ls.server.send.respond("references", [location(ls, "mod.py", 5, 10, 5, 13), location(ls, "other.py", 0, 6, 0, 9)])
    with caplog.at_level(logging.DEBUG, logger="pycrux.io.symbols"):
        ls.request_references("mod.py", 0, 6)
        ls.server.send.respond("references", [])
        ls.request_references("mod.py", 0, 6)
    assert "path=mod.py elapsed_ms=" in caplog.text
    assert "count=2 unique_files=2" in caplog.text
    assert "count=0" in caplog.text


def test_references_use_the_overridable_send_method(make_ls, sleeps) -> None:
    class Custom(type(make_ls())):
        def _send_references_request(self, relative_file_path, line, column):
            return [{"uri": (self.repo / "mod.py").as_uri(), "range": rng(1, 1, 1, 2)}]

    ls = make_ls({"mod.py": SOURCE}, ls_class=Custom)
    assert ls.request_references("mod.py", 0, 0)[0]["relativePath"] == "mod.py"


# --- request_completions ----------------------------------------------------------------------------------------------------


def test_request_completions_returns_unique_non_keyword_items(ls) -> None:
    foo = {"label": "foo", "kind": 3, "insertText": "foo", "detail": "def foo()"}
    ls.server.send.respond("completion", [foo, dict(foo), {"label": "if", "kind": 14, "insertText": "if"}, {"label": "bar", "kind": 2, "insertText": "bar"}])

    result = ls.request_completions("mod.py", 5, 4)

    assert sorted(result, key=lambda item: item["completionText"]) == [
        {"completionText": "bar", "kind": 2},
        {"completionText": "foo", "kind": 3, "detail": "def foo()"},
    ]
    (method, params) = ls.server.send.requests[0]
    assert method == "completion"
    assert params == {
        "position": {"line": 5, "character": 4},
        "textDocument": {"uri": (ls.repo / "mod.py").as_uri()},
        "context": {"triggerKind": 1},
    }


def test_request_completions_accepts_a_completion_list(ls) -> None:
    ls.server.send.respond("completion", {"isIncomplete": False, "items": [{"label": "x", "kind": 6, "insertText": "x"}]})
    assert ls.request_completions("mod.py", 0, 0) == [{"completionText": "x", "kind": 6}]


def test_request_completions_uses_text_edits(ls) -> None:
    item = {"kind": 3, "textEdit": {"newText": "edited", "range": rng(0, 0, 0, 0)}}
    ls.server.send.respond("completion", [item])
    assert ls.request_completions("mod.py", 0, 0) == [{"completionText": "edited", "kind": 3}]


def test_request_completions_uses_insert_text_without_a_label(ls) -> None:
    ls.server.send.respond("completion", [{"kind": 3, "insertText": "inserted"}])
    assert ls.request_completions("mod.py", 0, 0) == [{"completionText": "inserted", "kind": 3}]


def test_request_completions_without_response(ls) -> None:
    ls.server.send.respond("completion", None)
    assert ls.request_completions("mod.py", 0, 0) == []


def test_request_completions_incomplete_results(ls) -> None:
    ls.server.send.respond("completion", {"isIncomplete": True, "items": [{"label": "x", "kind": 6, "insertText": "x"}]})
    assert ls.request_completions("mod.py", 0, 0) == []
    assert ls.server.send.count("completion") == 30  # keeps asking while the server reports incomplete results

    ls.server.send.requests.clear()
    assert ls.request_completions("mod.py", 0, 0, allow_incomplete=True) == [{"completionText": "x", "kind": 6}]


def test_request_completions_requires_text_to_insert(ls) -> None:
    ls.server.send.respond("completion", [{"label": "x", "kind": 6}])
    with pytest.raises(AssertionError):
        ls.request_completions("mod.py", 0, 0)


# --- request_hover -----------------------------------------------------------------------------------------------------------


def test_request_hover(ls) -> None:
    ls.server.send.respond("hover", {"contents": {"kind": "markdown", "value": "docs"}, "range": rng(0, 0, 0, 3)})
    hover = ls.request_hover("mod.py", 0, 6)
    assert hover == {"contents": {"kind": "markdown", "value": "docs"}, "range": rng(0, 0, 0, 3)}
    assert ls.server.send.requests[0][1] == {
        "textDocument": {"uri": (ls.repo / "mod.py").as_uri()},
        "position": {"line": 0, "character": 6},
    }


def test_request_hover_accepts_plain_string_contents(ls) -> None:
    ls.server.send.respond("hover", {"contents": "plain docs"})
    assert ls.request_hover("mod.py", 0, 6) == {"contents": "plain docs"}


@pytest.mark.parametrize(
    "response",
    [None, {}, {"contents": ""}, {"contents": []}, {"contents": {"kind": "markdown", "value": ""}}, {"contents": {"kind": "markdown"}}],
)
def test_request_hover_without_useful_content(ls, response) -> None:
    ls.server.send.respond("hover", response)
    assert ls.request_hover("mod.py", 0, 6) is None


def test_request_hover_requires_a_dict_response(ls) -> None:
    ls.server.send.respond("hover", ["not", "a", "dict"])
    with pytest.raises(AssertionError):
        ls.request_hover("mod.py", 0, 6)


def test_request_hover_reuses_an_open_buffer(ls) -> None:
    ls.server.send.respond("hover", None)
    with ls.open_file("mod.py") as buffer:
        ls.request_hover("mod.py", 0, 6, file_buffer=buffer)
        assert buffer.ref_count == 1
    assert ls.server.send.requests[0][1]["textDocument"]["uri"] == buffer.uri


# --- request_signature_help ---------------------------------------------------------------------------------------------------


def test_request_signature_help(ls) -> None:
    response = {"signatures": [{"label": "bar(self)"}], "activeSignature": 0}
    ls.server.send.respond("signature_help", response)
    assert ls.request_signature_help("mod.py", 7, 15) == response
    assert ls.server.send.requests[0][1] == {
        "textDocument": {"uri": (ls.repo / "mod.py").as_uri()},
        "position": {"line": 7, "character": 15},
    }
    assert ls.open_file_buffers == {}


def test_request_signature_help_without_result(ls) -> None:
    ls.server.send.respond("signature_help", None)
    assert ls.request_signature_help("mod.py", 0, 0) is None


def test_request_signature_help_requires_a_dict(ls) -> None:
    ls.server.send.respond("signature_help", "text")
    with pytest.raises(AssertionError):
        ls.request_signature_help("mod.py", 0, 0)


# --- request_workspace_symbol -----------------------------------------------------------------------------------------------------


def test_request_workspace_symbol(ls) -> None:
    item = {"name": "Foo", "kind": 5, "location": location(ls, "mod.py", 0, 0, 2, 16)}
    ls.server.send.respond("workspace_symbol", [item])
    result = ls.request_workspace_symbol("Fo")
    assert result == [item]
    assert ls.server.send.requests == [("workspace_symbol", {"query": "Fo"})]


def test_request_workspace_symbol_without_result(ls) -> None:
    ls.server.send.respond("workspace_symbol", None)
    assert ls.request_workspace_symbol("x") is None
    ls.server.send.respond("workspace_symbol", [])
    assert ls.request_workspace_symbol("x") == []


@pytest.mark.parametrize("response", ["text", {"name": "x"}, ["not a dict"], [{"name": "Foo", "kind": 5}], [{"kind": 5, "location": {}}]])
def test_request_workspace_symbol_rejects_malformed_results(ls, response) -> None:
    ls.server.send.respond("workspace_symbol", response)
    with pytest.raises(AssertionError):
        ls.request_workspace_symbol("x")


# --- request_rename_symbol_edit -------------------------------------------------------------------------------------------------------


def test_request_rename_symbol_edit(ls) -> None:
    edit = {"changes": {(ls.repo / "mod.py").as_uri(): [{"range": rng(0, 6, 0, 9), "newText": "Bar"}]}}
    ls.server.send.respond("rename", edit)

    assert ls.request_rename_symbol_edit("mod.py", 0, 6, "Bar") == edit
    assert ls.server.send.requests == [
        (
            "rename",
            {
                "textDocument": {"uri": (ls.repo / "mod.py").as_uri()},
                "position": {"line": 0, "character": 6},
                "newName": "Bar",
            },
        )
    ]
    assert len(ls.server.notify.of("open")) == 1 and ls.open_file_buffers == {}


def test_request_rename_symbol_edit_when_rename_is_unsupported(ls) -> None:
    ls.server.send.respond("rename", None)
    assert ls.request_rename_symbol_edit("mod.py", 0, 6, "Bar") is None


def test_write_files_helper_creates_nested_files(tmp_path) -> None:
    write_files(tmp_path, {"a/b/c.txt": "x"})
    assert (tmp_path / "a" / "b" / "c.txt").read_text(encoding="utf-8") == "x"
