"""Tests for ``pycrux.io.buffers`` — ``LSPFileBuffer`` and the ``LanguageServerHandle`` protocol."""

import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol

import pytest

import pycrux.io.buffers as buffers_module
from pycrux.io.buffers import LanguageServerHandle, LSPFileBuffer

from . import conftest  # noqa: F401  (installs the third-party stand-ins first)


class RecordingNotify:
    def __init__(self) -> None:
        self.opened: list[dict] = []
        self.closed: list[dict] = []

    def did_open_text_document(self, params: dict) -> None:
        self.opened.append(params)

    def did_close_text_document(self, params: dict) -> None:
        self.closed.append(params)


@pytest.fixture
def language_server() -> SimpleNamespace:
    return SimpleNamespace(server=SimpleNamespace(notify=RecordingNotify()))


def _buffer(language_server, path: Path, **overrides) -> LSPFileBuffer:
    kwargs = dict(
        abs_path=path,
        uri=path.as_uri(),
        encoding="utf-8",
        version=0,
        language_id="python",
        ref_count=1,
        language_server=language_server,
    )
    kwargs.update(overrides)
    return LSPFileBuffer(**kwargs)


@pytest.fixture
def source_file(tmp_path) -> Path:
    path = tmp_path / "module.py"
    path.write_text("line one\nline two\n", encoding="utf-8")
    return path


# --- construction / opening --------------------------------------------------------------------------


def test_constructor_stores_its_arguments(language_server, source_file) -> None:
    buf = _buffer(language_server, source_file, version=3, ref_count=2, language_id="ruby", encoding="latin-1")
    assert buf.abs_path == source_file
    assert buf.uri == source_file.as_uri()
    assert (buf.version, buf.ref_count, buf.language_id, buf.encoding) == (3, 2, "ruby", "latin-1")
    assert buf.language_server is language_server


def test_opens_in_the_language_server_by_default(language_server, source_file) -> None:
    _buffer(language_server, source_file)
    (params,) = language_server.server.notify.opened
    assert params == {
        "textDocument": {
            "uri": source_file.as_uri(),
            "languageId": "python",
            "version": 0,
            "text": "line one\nline two\n",
        }
    }


def test_open_in_ls_false_defers_the_notification(language_server, source_file) -> None:
    buf = _buffer(language_server, source_file, open_in_ls=False)
    assert language_server.server.notify.opened == []
    buf.ensure_open_in_ls()
    assert len(language_server.server.notify.opened) == 1


def test_ensure_open_in_ls_is_idempotent(language_server, source_file) -> None:
    buf = _buffer(language_server, source_file)
    buf.ensure_open_in_ls()
    buf.ensure_open_in_ls()
    assert len(language_server.server.notify.opened) == 1


def test_open_notification_always_reports_version_zero(language_server, source_file) -> None:
    _buffer(language_server, source_file, version=7)
    assert language_server.server.notify.opened[0]["textDocument"]["version"] == 0


# --- close -----------------------------------------------------------------------------------------------


def test_close_notifies_only_when_the_file_was_opened(language_server, source_file) -> None:
    unopened = _buffer(language_server, source_file, open_in_ls=False)
    unopened.close()
    assert language_server.server.notify.closed == []

    opened = _buffer(language_server, source_file)
    opened.close()
    assert language_server.server.notify.closed == [{"textDocument": {"uri": source_file.as_uri()}}]


# --- contents ---------------------------------------------------------------------------------------------


def test_contents_are_read_lazily_and_cached(language_server, source_file) -> None:
    buf = _buffer(language_server, source_file, open_in_ls=False)
    assert buf._contents is None
    assert buf.contents == "line one\nline two\n"
    source_file.write_text("changed but same mtime", encoding="utf-8")
    os.utime(source_file, (buf._read_file_modified_date, buf._read_file_modified_date))
    assert buf.contents == "line one\nline two\n"  # served from the cache


def test_contents_are_reloaded_when_the_file_is_modified(language_server, source_file) -> None:
    buf = _buffer(language_server, source_file, open_in_ls=False)
    assert buf.contents == "line one\nline two\n"
    first_hash = buf.content_hash

    source_file.write_text("brand new", encoding="utf-8")
    newer = buf._read_file_modified_date + 5
    os.utime(source_file, (newer, newer))

    assert buf.contents == "brand new"
    assert buf.content_hash != first_hash


def test_contents_setter_changes_memory_only(language_server, source_file) -> None:
    buf = _buffer(language_server, source_file, open_in_ls=False)
    _ = buf.contents
    buf.contents = "edited in memory"
    assert buf.contents == "edited in memory"
    assert source_file.read_text(encoding="utf-8") == "line one\nline two\n"


def test_contents_setter_resets_the_hash(language_server, source_file) -> None:
    buf = _buffer(language_server, source_file, open_in_ls=False)
    before = buf.content_hash
    buf.contents = "other"
    assert buf.content_hash == hashlib.md5(b"other").hexdigest() != before


def test_contents_honour_the_configured_encoding(language_server, tmp_path) -> None:
    path = tmp_path / "latin.txt"
    path.write_bytes("café".encode("latin-1"))
    buf = _buffer(language_server, path, encoding="latin-1", open_in_ls=False)
    assert buf.contents == "café"


def test_contents_of_a_missing_file_raise(language_server, tmp_path) -> None:
    buf = _buffer(language_server, tmp_path / "missing.py", open_in_ls=False)
    with pytest.raises(FileNotFoundError):
        _ = buf.contents


# --- content_hash / split_lines ------------------------------------------------------------------------------


def test_content_hash_is_the_md5_of_the_encoded_contents(language_server, source_file) -> None:
    buf = _buffer(language_server, source_file, open_in_ls=False)
    assert buf.content_hash == hashlib.md5(b"line one\nline two\n").hexdigest()


def test_content_hash_is_cached_until_the_contents_change(language_server, source_file) -> None:
    buf = _buffer(language_server, source_file, open_in_ls=False)
    first = buf.content_hash
    assert buf._content_hash == first
    assert buf.content_hash is first


def test_content_hash_uses_the_buffer_encoding(language_server, tmp_path) -> None:
    path = tmp_path / "u.txt"
    path.write_text("é", encoding="utf-8")
    buf = _buffer(language_server, path, encoding="utf-8", open_in_ls=False)
    assert buf.content_hash == hashlib.md5("é".encode("utf-8")).hexdigest()


def test_split_lines(language_server, source_file) -> None:
    buf = _buffer(language_server, source_file, open_in_ls=False)
    assert buf.split_lines() == ["line one", "line two", ""]
    buf.contents = "single"
    assert buf.split_lines() == ["single"]
    buf.contents = ""
    assert buf.split_lines() == [""]


# --- LanguageServerHandle protocol ------------------------------------------------------------------------------


def test_language_server_handle_is_a_protocol_with_a_server_attribute() -> None:
    assert issubclass(LanguageServerHandle, Protocol)  # type: ignore[arg-type]
    assert "server" in LanguageServerHandle.__annotations__


def test_any_object_with_a_server_works_as_the_language_server(source_file) -> None:
    handle = SimpleNamespace(server=SimpleNamespace(notify=RecordingNotify()))
    buf = _buffer(handle, source_file)
    assert buf.language_server.server.notify.opened


def test_module_does_not_import_symbols() -> None:
    assert not hasattr(buffers_module, "SolidLanguageServer")
