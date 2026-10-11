"""Fixtures for the ``pycrux.io`` tests.

Importing this module installs the stand-ins for ``solidlsp`` & co. (see ``_stubs``) before any test module of
this folder imports ``pycrux.io.base``, ``pycrux.io.buffers`` or ``pycrux.io.symbols``.
"""

import pytest

from . import _stubs

_stubs.install()

from . import _fakes  # noqa: E402  (needs the stand-ins installed above)

if "solidlsp" in _stubs.STUBBED:
    from solidlsp.ls_config import LanguageServerConfig  # noqa: E402
    from solidlsp.settings import SolidLSPSettings  # noqa: E402


@pytest.fixture
def make_ls(tmp_path):
    """Factory for a started :class:`FakeLanguageServer` rooted in ``tmp_path / "repo"``.

    ``ls.repo`` is the (resolved) repository path, ``ls.server`` a :class:`FakeServer`.
    """
    _stubs.require_stubs()

    def factory(files: dict[str, str] | None = None, *, ignored_paths=(), ls_class=_fakes.FakeLanguageServer, started=True, **kwargs):
        repo = (tmp_path / "repo").resolve()
        repo.mkdir(exist_ok=True)
        _fakes.write_files(repo, files or {})
        settings = SolidLSPSettings(
            ls_resources_dir=str(tmp_path / "resources"),
            project_data_path=str(tmp_path / "project_data"),
        )
        config = LanguageServerConfig(ignored_paths=list(ignored_paths))
        ls = ls_class(config, str(repo), _fakes.make_launch_info(str(repo)), "python", settings, **kwargs)
        ls.server = _fakes.FakeServer()
        ls.server_started = started
        ls.repo = repo
        ls.settings = settings
        return ls

    return factory


@pytest.fixture
def sample_ls(make_ls):
    """A started language server for ``mod.py`` whose ``documentSymbol`` response is :func:`raw_symbols`."""
    ls = make_ls({"mod.py": _fakes.SOURCE})
    ls.server.send.respond("document_symbol", lambda _params: _fakes.raw_symbols())
    return ls
