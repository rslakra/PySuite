"""Tests for ``SolidLanguageServer`` — construction, lifecycle, file buffers, text edits and the caches."""

import logging
import os
import pickle
from pathlib import Path

import pytest

import pycrux.io.symbols as symbols
from pycrux.io.symbols import DocumentSymbols, SolidLanguageServer
from solidlsp.ls_config import Language, LanguageServerConfig
from solidlsp.settings import SolidLSPSettings

from . import _stubs
from ._fakes import SOURCE, FakeLanguageServer, FakeProcess, FakeServer, make_launch_info, raw_symbols, timeout_expired

_stubs.require_stubs()

SolidLSPException = symbols.SolidLSPException


# --- class constants and tiny helpers ------------------------------------------------------------------------


def test_class_constants() -> None:
    assert SolidLanguageServer.CACHE_FOLDER_NAME == "cache"
    assert SolidLanguageServer.RAW_DOCUMENT_SYMBOLS_CACHE_VERSION == 1
    assert SolidLanguageServer.RAW_DOCUMENT_SYMBOL_CACHE_FILENAME == "raw_document_symbols.pkl"
    assert SolidLanguageServer.RAW_DOCUMENT_SYMBOL_CACHE_FILENAME_LEGACY_FALLBACK == "document_symbols_cache_v23-06-25.pkl"
    assert SolidLanguageServer.DOCUMENT_SYMBOL_CACHE_VERSION == 4
    assert SolidLanguageServer.DOCUMENT_SYMBOL_CACHE_FILENAME == "document_symbols.pkl"


def test_is_ignored_dirname(make_ls) -> None:
    ls = make_ls()
    assert ls.is_ignored_dirname(".git") is True
    assert ls.is_ignored_dirname(".venv") is True
    assert ls.is_ignored_dirname("src") is False
    assert ls.is_ignored_dirname("node_modules") is False  # language-specific servers extend this


@pytest.mark.parametrize(
    ("line", "level"),
    [
        ("Some ERROR happened", logging.ERROR),
        ("java.lang.NullPointerException: x", logging.ERROR),
        ("E[2024-01-01] boom", logging.ERROR),
        ("Indexing complete", logging.INFO),
        ("", logging.INFO),
    ],
)
def test_determine_log_level(line: str, level: int) -> None:
    assert SolidLanguageServer._determine_log_level(line) == level


def test_language_enum_instance_and_implementation_support() -> None:
    language = FakeLanguageServer.get_language_enum_instance()
    assert isinstance(language, Language) and language.value == "python"
    assert FakeLanguageServer.supports_implementation_request() is False


# --- ls_resources_dir ----------------------------------------------------------------------------------------------


def test_ls_resources_dir_creates_the_directory(tmp_path) -> None:
    settings = SolidLSPSettings(ls_resources_dir=str(tmp_path / "res"), project_data_path=str(tmp_path))
    result = FakeLanguageServer.ls_resources_dir(settings)
    assert result == str(tmp_path / "res" / "FakeLanguageServer")
    assert Path(result).is_dir()


def test_ls_resources_dir_without_mkdir(tmp_path) -> None:
    settings = SolidLSPSettings(ls_resources_dir=str(tmp_path / "res"), project_data_path=str(tmp_path))
    result = FakeLanguageServer.ls_resources_dir(settings, mkdir=False)
    assert not Path(result).exists()


@pytest.fixture
def pre_migration_dir(tmp_path, monkeypatch) -> Path:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    monkeypatch.setattr(symbols, "__file__", str(package_dir / "symbols.py"))
    old = package_dir / "language_servers" / "static" / "FakeLanguageServer"
    old.mkdir(parents=True)
    (old / "server.bin").write_text("binary", encoding="utf-8")
    return old


def test_ls_resources_dir_migrates_old_resources(tmp_path, pre_migration_dir) -> None:
    settings = SolidLSPSettings(ls_resources_dir=str(tmp_path / "res"), project_data_path=str(tmp_path))
    result = Path(FakeLanguageServer.ls_resources_dir(settings))
    assert (result / "server.bin").read_text(encoding="utf-8") == "binary"
    assert not pre_migration_dir.exists()


def test_ls_resources_dir_removes_the_old_directory_and_keeps_the_new_one(tmp_path, pre_migration_dir) -> None:
    new = tmp_path / "res" / "FakeLanguageServer"
    new.mkdir(parents=True)
    (new / "downloaded.bin").write_text("fresh download", encoding="utf-8")
    settings = SolidLSPSettings(ls_resources_dir=str(tmp_path / "res"), project_data_path=str(tmp_path))

    result = Path(FakeLanguageServer.ls_resources_dir(settings))

    assert result == new
    assert (new / "downloaded.bin").read_text(encoding="utf-8") == "fresh download"  # regression: used to be deleted
    assert not pre_migration_dir.exists()


# --- create ----------------------------------------------------------------------------------------------------------


class CreatableLanguageServer(FakeLanguageServer):
    """``create`` assumes the ``(config, repository_root_path, solidlsp_settings)`` constructor signature."""

    def __init__(self, config, repository_root_path, solidlsp_settings) -> None:
        super().__init__(config, repository_root_path, make_launch_info(repository_root_path), "python", solidlsp_settings)


@pytest.fixture
def creatable(monkeypatch, tmp_path):
    monkeypatch.setattr(Language, "ls_class", CreatableLanguageServer)
    monkeypatch.chdir(tmp_path)  # the default settings use relative cache/resource directories
    return tmp_path


def test_create_builds_the_language_specific_server(creatable) -> None:
    (creatable / "repo").mkdir()
    settings = SolidLSPSettings(ls_resources_dir=str(creatable / "res"), project_data_path=str(creatable / "pd"))

    ls = SolidLanguageServer.create(LanguageServerConfig(), str(creatable / "repo"), timeout=12.5, solidlsp_settings=settings)

    assert type(ls) is CreatableLanguageServer
    assert ls.server.timeout == 12.5
    assert ls.repository_root_path == str(creatable / "repo")


def test_create_makes_the_repository_path_absolute(creatable) -> None:
    ls = SolidLanguageServer.create(LanguageServerConfig(), "relative/repo")
    assert os.path.isabs(ls.repository_root_path)
    assert ls.repository_root_path == str(creatable / "relative" / "repo")


def test_create_uses_default_settings_and_no_timeout(creatable) -> None:
    ls = SolidLanguageServer.create(LanguageServerConfig(), "repo")
    assert isinstance(ls._solidlsp_settings, SolidLSPSettings)
    assert ls.server.timeout is None


# --- constructor -------------------------------------------------------------------------------------------------------


def test_constructor_initialises_state_and_cache_directory(make_ls) -> None:
    ls = make_ls(started=False)
    assert ls.language_id == "python"
    assert ls.repository_root_path == str(ls.repo)
    assert ls.server_started is False
    assert ls.open_file_buffers == {}
    assert ls._request_timeout is None
    assert ls._has_waited_for_cross_file_references is False
    assert ls.cache_dir == Path(ls.settings.project_data_path) / "cache" / "python"
    assert ls.cache_dir.is_dir()
    assert ls._raw_document_symbols_cache == {} and ls._document_symbols_cache == {}
    assert ls._raw_document_symbols_cache_is_modified is False and ls._document_symbols_cache_is_modified is False
    assert ls._ls_resources_dir == str(Path(ls.settings.ls_resources_dir) / "FakeLanguageServer")


def test_constructor_reads_language_specific_settings(tmp_path) -> None:
    settings = SolidLSPSettings(
        ls_resources_dir=str(tmp_path / "res"), project_data_path=str(tmp_path / "pd"), ls_specific={"ls_path": "/opt/ls"}
    )
    ls = FakeLanguageServer(LanguageServerConfig(), str(tmp_path), make_launch_info(str(tmp_path)), "python", settings)
    assert ls._custom_settings == {"ls_path": "/opt/ls"}
    assert ls._encoding == "utf-8"


def test_constructor_passes_the_launch_info_to_the_process(tmp_path) -> None:
    settings = SolidLSPSettings(ls_resources_dir=str(tmp_path / "res"), project_data_path=str(tmp_path / "pd"))
    config = LanguageServerConfig(start_independent_lsp_process=True)
    launch = make_launch_info(str(tmp_path))
    ls = FakeLanguageServer(config, str(tmp_path), launch, "python", settings)
    assert ls.server.launch_info is launch
    assert ls.server.start_independent_lsp_process is True
    assert ls.server.determine_log_level == ls._determine_log_level
    assert ls.server.logger is None  # LSP tracing is off by default


def test_constructor_logs_lsp_traffic_when_tracing_is_enabled(tmp_path, caplog) -> None:
    settings = SolidLSPSettings(ls_resources_dir=str(tmp_path / "res"), project_data_path=str(tmp_path / "pd"))
    ls = FakeLanguageServer(LanguageServerConfig(trace_lsp_communication=True), str(tmp_path), make_launch_info(str(tmp_path)), "python", settings)
    with caplog.at_level(logging.DEBUG, logger="pycrux.io.symbols"):
        ls.server.logger("client", "server", {"method": "initialize"})
    assert "LSP: client -> server: {'method': 'initialize'}" in caplog.text


def test_constructor_requires_a_dependency_provider_without_launch_info(tmp_path) -> None:
    settings = SolidLSPSettings(ls_resources_dir=str(tmp_path / "res"), project_data_path=str(tmp_path / "pd"))
    with pytest.raises(NotImplementedError, match="FakeLanguageServer must implement _create_dependency_provider"):
        FakeLanguageServer(LanguageServerConfig(), str(tmp_path), None, "python", settings)


def test_constructor_builds_the_launch_info_from_the_dependency_provider(tmp_path) -> None:
    class Provider(symbols.LanguageServerDependencyProvider):
        def create_launch_command(self) -> list[str]:
            return ["my-ls", "--stdio"]

        def create_launch_command_env(self) -> dict[str, str]:
            return {"LS_HOME": "/opt"}

    class ProvidedLanguageServer(FakeLanguageServer):
        def _create_dependency_provider(self):
            return Provider(self._custom_settings, self._ls_resources_dir)

    settings = SolidLSPSettings(ls_resources_dir=str(tmp_path / "res"), project_data_path=str(tmp_path / "pd"))
    ls = ProvidedLanguageServer(LanguageServerConfig(), str(tmp_path), None, "python", settings)

    launch = ls.server.launch_info
    assert (launch.cmd, launch.cwd, launch.env) == (["my-ls", "--stdio"], str(tmp_path), {"LS_HOME": "/opt"})
    assert isinstance(ls._dependency_provider, Provider)


def test_constructor_builds_the_ignore_spec_from_the_configured_paths(make_ls) -> None:
    ls = make_ls(ignored_paths=["build", "*.generated.py", "build"])
    spec = ls.get_ignore_spec()
    assert spec.match_file("build/output.py")
    assert spec.match_file("pkg/mod.generated.py")
    assert not spec.match_file("pkg/mod.py")


# --- small accessors ---------------------------------------------------------------------------------------------------


def test_wait_time_for_cross_file_referencing_defaults_to_two_seconds(make_ls) -> None:
    assert make_ls()._get_wait_time_for_cross_file_referencing() == 2


def test_set_request_timeout_is_forwarded_to_the_process(make_ls) -> None:
    ls = make_ls()
    ls.set_request_timeout(30.0)
    assert ls.server.timeout == 30.0
    ls.set_request_timeout(None)
    assert ls.server.timeout is None


def test_source_filename_matcher_comes_from_the_language(make_ls) -> None:
    matcher = make_ls().get_source_fn_matcher()
    assert matcher.is_relevant_filename("/repo/a.py") is True
    assert matcher.is_relevant_filename("/repo/a.txt") is False


def test_language_id_for_file_defaults_to_the_server_language(make_ls) -> None:
    assert make_ls()._get_language_id_for_file("any/file.xyz") == "python"


def test_properties_and_is_running(make_ls) -> None:
    ls = make_ls()
    assert ls.language_server is ls
    assert ls.handler is ls.server
    assert ls.is_running() is True
    ls.server.running = False
    assert ls.is_running() is False


def test_default_dependency_provider_is_not_implemented(make_ls) -> None:
    with pytest.raises(NotImplementedError):
        make_ls()._create_dependency_provider()


# --- is_ignored_path -----------------------------------------------------------------------------------------------------


@pytest.fixture
def tree_ls(make_ls):
    return make_ls(
        {
            "src/app.py": "x = 1\n",
            "src/notes.txt": "text\n",
            ".hidden/secret.py": "y = 2\n",
            "build/out.py": "z = 3\n",
            "src/.cache/data.py": "w = 4\n",
        },
        ignored_paths=["build"],
    )


def test_is_ignored_path_accepts_normal_source_files(tree_ls) -> None:
    assert tree_ls.is_ignored_path("src/app.py") is False


def test_is_ignored_path_requires_the_path_to_exist(tree_ls) -> None:
    with pytest.raises(FileNotFoundError, match="the ignore check cannot be performed"):
        tree_ls.is_ignored_path("src/missing.py")


def test_is_ignored_path_ignores_unsupported_file_types_by_default(tree_ls) -> None:
    assert tree_ls.is_ignored_path("src/notes.txt") is True
    assert tree_ls.is_ignored_path("src/notes.txt", ignore_unsupported_files=False) is False


@pytest.mark.parametrize("path", [".hidden/secret.py", "src/.cache/data.py", ".hidden"])
def test_is_ignored_path_ignores_dot_directories(tree_ls, path: str) -> None:
    assert tree_ls.is_ignored_path(path, ignore_unsupported_files=False) is True


def test_is_ignored_path_applies_configured_patterns(tree_ls) -> None:
    assert tree_ls.is_ignored_path("build/out.py") is True
    assert tree_ls.is_ignored_path("build") is True


def test_is_ignored_path_does_not_apply_directory_rules_to_the_file_name(make_ls) -> None:
    ls = make_ls({".env.py": "a = 1\n"})
    assert ls.is_ignored_path(".env.py") is False  # only directory parts are checked against is_ignored_dirname


def test_is_ignored_path_ignores_empty_path_parts(tree_ls) -> None:
    assert tree_ls.is_ignored_path("src//app.py") is False


# --- start / stop / shutdown ------------------------------------------------------------------------------------------------


def test_start_server_process_marks_the_server_started(make_ls) -> None:
    ls = make_ls(started=False)
    before = FakeLanguageServer.started_calls
    ls._start_server_process()
    assert ls.server_started is True
    assert FakeLanguageServer.started_calls == before + 1


def test_start_returns_self_and_starts_the_process(make_ls) -> None:
    ls = make_ls(started=False)
    assert ls.start() is ls
    assert ls.server_started is True


def test_stop_delegates_to_shutdown_with_the_timeout(make_ls, monkeypatch) -> None:
    ls = make_ls()
    calls: list[float] = []
    monkeypatch.setattr(ls, "_shutdown", lambda timeout: calls.append(timeout))
    ls.stop()
    ls.stop(shutdown_timeout=7.5)
    assert calls == [2.0, 7.5]


def test_stop_never_raises(make_ls, monkeypatch, caplog) -> None:
    ls = make_ls()

    def explode(timeout: float) -> None:
        raise RuntimeError("kaboom")

    monkeypatch.setattr(ls, "_shutdown", explode)
    with caplog.at_level(logging.WARNING, logger="pycrux.io.symbols"):
        ls.stop()
    assert "Exception while shutting down language server: kaboom" in caplog.text


def test_start_server_context_manager_starts_and_stops(make_ls, monkeypatch) -> None:
    ls = make_ls(started=False)
    stopped: list[bool] = []
    monkeypatch.setattr(ls, "stop", lambda *a, **k: stopped.append(True))
    with ls.start_server() as server:
        assert server is ls and ls.server_started is True
        assert stopped == []
    assert stopped == [True]


def test_shutdown_is_skipped_when_the_server_is_not_running(make_ls) -> None:
    ls = make_ls()
    ls.server.running = False
    ls._shutdown()
    assert ls.server.shutdown_calls == 0 and not ls.server.process.terminated


def test_shutdown_is_skipped_without_a_process(make_ls) -> None:
    ls = make_ls()
    ls.server.process = None
    ls._shutdown()
    assert ls.server.shutdown_calls == 0


def test_shutdown_terminates_gracefully(make_ls) -> None:
    ls = make_ls()
    process = ls.server.process
    ls._shutdown(timeout=3.0)
    assert ls.server.shutdown_calls == 1
    assert process.stdin.closed is True
    assert process.terminated is True and process.killed is False
    assert process.wait_calls == [3.0]


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_shutdown_survives_an_lsp_shutdown_failure(make_ls) -> None:
    ls = make_ls()
    ls.server.shutdown_error = RuntimeError("no response")
    ls._shutdown()
    assert ls.server.process.terminated is True


def test_shutdown_does_not_close_an_already_closed_stdin(make_ls) -> None:
    ls = make_ls()
    ls.server.process.stdin.closed = True
    ls._shutdown()
    assert ls.server.process.terminated is True


def test_shutdown_handles_a_process_without_stdin(make_ls) -> None:
    ls = make_ls()
    ls.server.process.stdin = None
    ls._shutdown()
    assert ls.server.process.terminated is True


def test_shutdown_kills_the_process_when_termination_times_out(make_ls) -> None:
    ls = make_ls()
    ls.server.process = FakeProcess(wait_results=[timeout_expired(), 0])
    ls._shutdown(timeout=1.0)
    assert ls.server.process.killed is True
    assert ls.server.process.wait_calls == [1.0, 2.0]


def test_shutdown_reports_a_process_that_cannot_be_killed(make_ls, caplog) -> None:
    ls = make_ls()
    ls.server.process = FakeProcess(wait_results=[timeout_expired(), timeout_expired()])
    with caplog.at_level(logging.ERROR, logger="pycrux.io.symbols"):
        ls._shutdown()
    assert "could not be killed within timeout" in caplog.text


def test_shutdown_logs_unexpected_wait_errors(make_ls, caplog) -> None:
    ls = make_ls()
    ls.server.process = FakeProcess(wait_results=[OSError("weird")])
    with caplog.at_level(logging.ERROR, logger="pycrux.io.symbols"):
        ls._shutdown()
    assert "Error during process shutdown: weird" in caplog.text


# --- open_file / _open_file_context ---------------------------------------------------------------------------------------------


def test_open_file_requires_a_started_server(make_ls) -> None:
    ls = make_ls({"mod.py": SOURCE}, started=False)
    with pytest.raises(SolidLSPException, match="Language Server not started"):
        with ls.open_file("mod.py"):
            pass


def test_open_file_registers_notifies_and_cleans_up(sample_ls) -> None:
    ls = sample_ls
    uri = (ls.repo / "mod.py").as_uri()
    with ls.open_file("mod.py") as buffer:
        assert buffer.uri == uri and buffer.ref_count == 1
        assert ls.open_file_buffers == {uri: buffer}
        assert len(ls.server.notify.of("open")) == 1
        assert buffer.language_id == "python" and buffer.encoding == "utf-8"
    assert ls.open_file_buffers == {}
    assert ls.server.notify.of("close") == [{"textDocument": {"uri": uri}}]


def test_open_file_is_reference_counted_for_nested_use(sample_ls) -> None:
    ls = sample_ls
    with ls.open_file("mod.py") as outer:
        with ls.open_file("mod.py") as inner:
            assert inner is outer and outer.ref_count == 2
        assert outer.ref_count == 1
        assert ls.server.notify.of("close") == []
        assert len(ls.open_file_buffers) == 1
    assert ls.open_file_buffers == {}
    assert len(ls.server.notify.of("close")) == 1
    assert len(ls.server.notify.of("open")) == 1  # the LS was only notified once


def test_open_file_can_defer_the_open_notification(sample_ls) -> None:
    ls = sample_ls
    with ls.open_file("mod.py", open_in_ls=False) as buffer:
        assert ls.server.notify.of("open") == []
        with ls.open_file("mod.py") as again:  # a later request upgrades the buffer
            assert again is buffer
        assert len(ls.server.notify.of("open")) == 1
    assert len(ls.server.notify.of("close")) == 1


def test_open_file_cleans_up_when_the_body_raises(sample_ls) -> None:
    ls = sample_ls
    with pytest.raises(RuntimeError):
        with ls.open_file("mod.py"):
            raise RuntimeError("boom")
    # regression: the buffer used to stay registered (and open in the LS) after an error
    assert ls.open_file_buffers == {}
    assert len(ls.server.notify.of("close")) == 1


def test_open_file_nested_error_releases_only_the_inner_reference(sample_ls) -> None:
    ls = sample_ls
    with ls.open_file("mod.py") as outer:
        with pytest.raises(RuntimeError):
            with ls.open_file("mod.py"):
                raise RuntimeError("boom")
        assert outer.ref_count == 1
        assert len(ls.open_file_buffers) == 1
    assert ls.open_file_buffers == {}


def test_open_file_context_with_a_matching_buffer(sample_ls) -> None:
    ls = sample_ls
    with ls.open_file("mod.py", open_in_ls=False) as buffer:
        with ls._open_file_context("mod.py", file_buffer=buffer) as same:
            assert same is buffer
        assert buffer.ref_count == 1  # an existing buffer is reused without touching the reference count
        assert len(ls.server.notify.of("open")) == 1  # ... but it is opened in the LS on request


def test_open_file_context_can_skip_opening_in_the_language_server(sample_ls) -> None:
    ls = sample_ls
    with ls.open_file("mod.py", open_in_ls=False) as buffer:
        with ls._open_file_context("mod.py", file_buffer=buffer, open_in_ls=False):
            pass
        assert ls.server.notify.of("open") == []


def test_open_file_context_rejects_a_buffer_for_another_file(make_ls) -> None:
    ls = make_ls({"a.py": "a = 1\n", "b.py": "b = 2\n"})
    with ls.open_file("a.py") as buffer:
        with pytest.raises(AssertionError, match="Inconsistency between provided"):
            with ls._open_file_context("b.py", file_buffer=buffer):
                pass


def test_open_file_context_opens_the_file_itself_without_a_buffer(sample_ls) -> None:
    ls = sample_ls
    with ls._open_file_context("mod.py") as buffer:
        assert buffer.uri in ls.open_file_buffers
    assert ls.open_file_buffers == {}


# --- text edits ---------------------------------------------------------------------------------------------------------------------


def test_insert_text_at_position(sample_ls) -> None:
    ls = sample_ls
    with ls.open_file("mod.py") as buffer:
        position = ls.insert_text_at_position("mod.py", 0, 0, "# header\n")

        assert position == {"line": 1, "character": 0}
        assert buffer.contents.startswith("# header\nclass Foo:")
        assert buffer.version == 1
        (change,) = ls.server.notify.of("change")
        assert change == {
            "textDocument": {"version": 1, "uri": buffer.uri},
            "contentChanges": [
                {"range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}}, "text": "# header\n"}
            ],
        }
    assert (ls.repo / "mod.py").read_text(encoding="utf-8") == SOURCE  # in-memory change only


def test_insert_text_returns_the_updated_cursor_position(sample_ls) -> None:
    with sample_ls.open_file("mod.py"):
        assert sample_ls.insert_text_at_position("mod.py", 4, 4, "ab") == {"line": 4, "character": 6}
        assert sample_ls.insert_text_at_position("mod.py", 4, 4, "x\nyz") == {"line": 5, "character": 2}


def test_insert_text_requires_a_started_server(make_ls) -> None:
    ls = make_ls({"mod.py": SOURCE}, started=False)
    with pytest.raises(SolidLSPException, match="Language Server not started"):
        ls.insert_text_at_position("mod.py", 0, 0, "x")


def test_insert_text_requires_the_file_to_be_open(sample_ls) -> None:
    with pytest.raises(AssertionError):
        sample_ls.insert_text_at_position("mod.py", 0, 0, "x")


def test_delete_text_between_positions(sample_ls) -> None:
    ls = sample_ls
    start, end = {"line": 0, "character": 6}, {"line": 0, "character": 9}
    with ls.open_file("mod.py") as buffer:
        deleted = ls.delete_text_between_positions("mod.py", start, end)

        assert deleted == "Foo"
        assert buffer.contents.splitlines()[0] == "class :"
        assert buffer.version == 1
        (change,) = ls.server.notify.of("change")
        assert change["contentChanges"] == [{"range": {"start": start, "end": end}, "text": ""}]


def test_delete_text_requires_a_started_server_and_an_open_file(make_ls) -> None:
    ls = make_ls({"mod.py": SOURCE}, started=False)
    pos = {"line": 0, "character": 0}
    with pytest.raises(SolidLSPException, match="Language Server not started"):
        ls.delete_text_between_positions("mod.py", pos, pos)
    ls.server_started = True
    with pytest.raises(AssertionError):
        ls.delete_text_between_positions("mod.py", pos, pos)


def test_apply_text_edits_to_file(sample_ls) -> None:
    ls = sample_ls
    edits = [
        {"range": {"start": {"line": 0, "character": 6}, "end": {"line": 0, "character": 9}}, "newText": "Renamed"},
        {"range": {"start": {"line": 4, "character": 4}, "end": {"line": 4, "character": 10}}, "newText": "util"},
        {"range": {"start": {"line": 8, "character": 4}, "end": {"line": 8, "character": 10}}, "newText": "util"},
    ]
    with ls.open_file("mod.py") as buffer:
        ls.apply_text_edits_to_file("mod.py", edits)
        lines = buffer.contents.splitlines()
    assert lines[0] == "class Renamed:"
    assert lines[4] == "def util():"
    assert lines[8] == "x = util()"
    # edits are applied from the end of the file backwards: the bottom edit is notified first
    changes = ls.server.notify.of("change")
    assert [c["contentChanges"][0]["range"]["start"]["line"] for c in changes if c["contentChanges"][0]["text"]] == [8, 4, 0]


def test_apply_text_edits_without_edits_is_a_noop(sample_ls) -> None:
    sample_ls.apply_text_edits_to_file("mod.py", [])
    assert sample_ls.server.notify.of("change") == []


# --- reading files ------------------------------------------------------------------------------------------------------------------------


def test_retrieve_full_file_content_accepts_relative_and_absolute_paths(sample_ls) -> None:
    assert sample_ls.retrieve_full_file_content("mod.py") == SOURCE
    assert sample_ls.retrieve_full_file_content(str(sample_ls.repo / "mod.py")) == SOURCE
    assert sample_ls.open_file_buffers == {}


def test_retrieve_content_around_line(sample_ls) -> None:
    result = sample_ls.retrieve_content_around_line("mod.py", 5, context_lines_before=1, context_lines_after=2)
    assert result.contents == SOURCE
    assert (result.line, result.context_lines_before, result.context_lines_after) == (5, 1, 2)
    assert result.source_file_path == "mod.py"
    default = sample_ls.retrieve_content_around_line("mod.py", 0)
    assert (default.context_lines_before, default.context_lines_after) == (0, 0)


# --- cache versions ----------------------------------------------------------------------------------------------------------------------------


def test_cache_fingerprint_and_versions_default(make_ls) -> None:
    ls = make_ls()
    assert ls._document_symbols_cache_fingerprint() is None
    assert ls._document_symbols_cache_version() == 4
    assert ls._raw_document_symbols_cache_version() == (1, 1)


def test_cache_versions_include_the_ls_specific_version(make_ls) -> None:
    ls = make_ls(cache_version_raw_document_symbols=7)
    assert ls._raw_document_symbols_cache_version() == (1, 7)


def test_cache_versions_include_the_fingerprint(make_ls) -> None:
    class Fingerprinted(FakeLanguageServer):
        def _document_symbols_cache_fingerprint(self):
            return ("flags", 3)

    ls = make_ls(ls_class=Fingerprinted)
    assert ls._document_symbols_cache_version() == (4, ("flags", 3))
    assert ls._raw_document_symbols_cache_version() == (1, 1, ("flags", 3))


# --- saving and loading the caches -----------------------------------------------------------------------------------------------------------------


def _populate(ls) -> None:
    ls.request_document_symbols("mod.py")
    assert ls._raw_document_symbols_cache_is_modified and ls._document_symbols_cache_is_modified


def test_save_cache_skips_unmodified_caches(sample_ls) -> None:
    sample_ls.save_cache()
    assert list(sample_ls.cache_dir.iterdir()) == []


def test_save_cache_writes_both_caches_and_clears_the_flags(sample_ls) -> None:
    _populate(sample_ls)
    sample_ls.save_cache()
    assert (sample_ls.cache_dir / "raw_document_symbols.pkl").is_file()
    assert (sample_ls.cache_dir / "document_symbols.pkl").is_file()
    assert not sample_ls._raw_document_symbols_cache_is_modified
    assert not sample_ls._document_symbols_cache_is_modified


def test_saved_caches_are_loaded_by_a_new_server(sample_ls, make_ls) -> None:
    _populate(sample_ls)
    sample_ls.save_cache()

    fresh = make_ls({"mod.py": SOURCE})

    assert set(fresh._raw_document_symbols_cache) == {"mod.py"}
    assert set(fresh._document_symbols_cache) == {"mod.py"}
    file_hash, document = fresh._document_symbols_cache["mod.py"]
    assert isinstance(document, DocumentSymbols)
    assert [s["name"] for s in document.iter_symbols()] == ["Foo", "bar", "helper", "x"]
    fresh.server.send.respond("document_symbol", lambda p: pytest.fail("served from the cache"))
    assert fresh.request_document_symbols("mod.py") is document


def test_caches_with_another_version_are_ignored(sample_ls, make_ls) -> None:
    _populate(sample_ls)
    sample_ls.save_cache()
    fresh = make_ls({"mod.py": SOURCE}, cache_version_raw_document_symbols=99)
    assert fresh._raw_document_symbols_cache == {}
    assert set(fresh._document_symbols_cache) == {"mod.py"}  # the high-level cache has its own version


def test_corrupt_cache_files_are_ignored(sample_ls, make_ls, caplog) -> None:
    sample_ls.cache_dir.mkdir(parents=True, exist_ok=True)
    (sample_ls.cache_dir / "raw_document_symbols.pkl").write_bytes(b"not a pickle")
    (sample_ls.cache_dir / "document_symbols.pkl").write_bytes(b"not a pickle")
    with caplog.at_level(logging.WARNING, logger="pycrux.io.symbols"):
        fresh = make_ls({"mod.py": SOURCE})
    assert fresh._raw_document_symbols_cache == {} and fresh._document_symbols_cache == {}
    assert caplog.text.count("Ignoring cache") == 2


def test_save_errors_are_logged_and_keep_the_modified_flags(sample_ls, monkeypatch, caplog) -> None:
    _populate(sample_ls)

    def failing_save(*_args) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(symbols, "save_cache", failing_save)
    with caplog.at_level(logging.ERROR, logger="pycrux.io.symbols"):
        sample_ls.save_cache()
    assert caplog.text.count("disk full") == 2
    assert sample_ls._raw_document_symbols_cache_is_modified and sample_ls._document_symbols_cache_is_modified


# --- legacy cache migration -------------------------------------------------------------------------------------------------------------------------


def _legacy_path(tmp_path: Path) -> Path:
    cache_dir = tmp_path / "project_data" / "cache" / "python"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "document_symbols_cache_v23-06-25.pkl"


def test_legacy_cache_is_migrated(tmp_path, make_ls) -> None:
    legacy = _legacy_path(tmp_path)
    root = {"name": "Foo"}
    legacy.write_bytes(
        pickle.dumps(
            {
                "a.py-True": ("hash-a", ([root, {"name": "child"}], [root])),
                "b.py-False": ("hash-b", ([{"name": "ignored"}], [{"name": "ignored"}])),
                "c.py-True": ("hash-c", ([], [])),
            }
        )
    )

    ls = make_ls()

    assert ls._raw_document_symbols_cache == {"a.py": ("hash-a", [root]), "c.py": ("hash-c", [])}
    assert not legacy.exists()
    assert (ls.cache_dir / "raw_document_symbols.pkl").is_file()  # the migrated cache was saved in the new format
    assert ls._raw_document_symbols_cache_is_modified is False


def test_unreadable_legacy_cache_is_reported_and_kept(tmp_path, make_ls, caplog) -> None:
    legacy = _legacy_path(tmp_path)
    legacy.write_bytes(b"garbage")
    with caplog.at_level(logging.ERROR, logger="pycrux.io.symbols"):
        ls = make_ls()
    assert "Error during cache migration" in caplog.text
    assert ls._raw_document_symbols_cache == {}
    assert legacy.exists()


def test_the_legacy_cache_is_not_used_when_a_new_cache_exists(tmp_path, sample_ls, make_ls) -> None:
    _populate(sample_ls)
    sample_ls.save_cache()
    legacy = _legacy_path(tmp_path)
    legacy.write_bytes(pickle.dumps({"zzz.py-True": ("h", ([], []))}))

    fresh = make_ls({"mod.py": SOURCE})

    assert set(fresh._raw_document_symbols_cache) == {"mod.py"}
    assert legacy.exists()


# --- unrelated to fakes: the helper module stays importable ------------------------------------------------------------------------------------------------


def test_fake_server_double_is_usable_standalone() -> None:
    server = FakeServer()
    server.send.respond("hover", {"contents": "x"})
    assert server.send.hover({"p": 1}) == {"contents": "x"}
    assert server.send.requests == [("hover", {"p": 1})]
    assert raw_symbols()[0]["name"] == "Foo"
