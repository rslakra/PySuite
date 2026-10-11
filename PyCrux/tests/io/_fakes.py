"""Test doubles for the language-server tests (``symbols`` module).

Imported only after ``conftest`` installed the third-party stand-ins.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable

from pycrux.io.symbols import SolidLanguageServer
from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo

# A small python file and the raw ``textDocument/documentSymbol`` response a server would return for it.
SOURCE_LINES = [
    "class Foo:",  # 0
    "    def bar(self):",  # 1
    "        return 1",  # 2
    "",  # 3
    "def helper():",  # 4
    "    foo = Foo()",  # 5
    "    foo.status = 1",  # 6
    "    return foo.bar()",  # 7
    "x = helper()",  # 8
]
SOURCE = "\n".join(SOURCE_LINES) + "\n"


def rng(start_line: int, start_char: int, end_line: int, end_char: int) -> dict:
    return {
        "start": {"line": start_line, "character": start_char},
        "end": {"line": end_line, "character": end_char},
    }


def raw_symbols() -> list[dict]:
    """Fresh ``DocumentSymbol``-shaped dictionaries (the code under test mutates them)."""
    return [
        {
            "name": "Foo",
            "kind": 5,
            "range": rng(0, 0, 2, 16),
            "selectionRange": rng(0, 6, 0, 9),
            "children": [
                {
                    "name": "bar",
                    "kind": 6,
                    "range": rng(1, 4, 2, 16),
                    "selectionRange": rng(1, 8, 1, 11),
                }
            ],
        },
        {
            "name": "helper",
            "kind": 12,
            "range": rng(4, 0, 7, 20),
            "selectionRange": rng(4, 4, 4, 10),
        },
        {
            "name": "x",
            "kind": 13,
            "range": rng(8, 0, 8, 12),
            "selectionRange": rng(8, 0, 8, 1),
        },
    ]


class FakeSend:
    """``server.send``: every attribute is a request method returning a preset response."""

    def __init__(self) -> None:
        self.responses: dict[str, Any] = {}
        self.requests: list[tuple[str, Any]] = []

    def respond(self, method: str, response: Any) -> None:
        self.responses[method] = response

    def _call(self, method: str, params: Any) -> Any:
        self.requests.append((method, params))
        response = self.responses.get(method)
        if isinstance(response, BaseException):
            raise response
        if callable(response):
            return response(params)
        return response

    def __getattr__(self, method: str) -> Callable[[Any], Any]:
        if method.startswith("_"):
            raise AttributeError(method)
        return lambda params: self._call(method, params)

    def count(self, method: str) -> int:
        return sum(1 for name, _ in self.requests if name == method)


class FakeNotify:
    def __init__(self) -> None:
        self.events: list[tuple[str, Any]] = []

    def did_open_text_document(self, params: Any) -> None:
        self.events.append(("open", params))

    def did_close_text_document(self, params: Any) -> None:
        self.events.append(("close", params))

    def did_change_text_document(self, params: Any) -> None:
        self.events.append(("change", params))

    def of(self, kind: str) -> list[Any]:
        return [params for event, params in self.events if event == kind]


class FakeProcess:
    """Stands in for ``subprocess.Popen`` in the shutdown tests."""

    def __init__(self, *, wait_results: list[Any] | None = None) -> None:
        self.pid = 4242
        self.stdin = FakeStdin()
        self.terminated = False
        self.killed = False
        self.wait_calls: list[float | None] = []
        self._wait_results = list(wait_results if wait_results is not None else [0])

    def poll(self) -> int | None:
        return None

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls.append(timeout)
        result = self._wait_results.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result


class FakeStdin:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def timeout_expired() -> subprocess.TimeoutExpired:
    return subprocess.TimeoutExpired(cmd="fake", timeout=1)


class FakeServer:
    """Replacement for the ``LanguageServerProcess`` held in ``ls.server``."""

    def __init__(self) -> None:
        self.send = FakeSend()
        self.notify = FakeNotify()
        self.running = True
        self.process: FakeProcess | None = FakeProcess()
        self.timeout: float | None = None
        self.shutdown_calls = 0
        self.shutdown_error: Exception | None = None

    def is_running(self) -> bool:
        return self.running

    def shutdown(self) -> None:
        self.shutdown_calls += 1
        if self.shutdown_error is not None:
            raise self.shutdown_error

    def set_request_timeout(self, timeout: float | None) -> None:
        self.timeout = timeout


class FakeLanguageServer(SolidLanguageServer):
    """Concrete ``SolidLanguageServer`` with the process replaced by :class:`FakeServer`."""

    started_calls = 0

    def _start_server(self) -> None:
        type(self).started_calls += 1


def make_launch_info(repo: str) -> ProcessLaunchInfo:
    return ProcessLaunchInfo(cmd=["fake-ls"], cwd=repo)


def write_files(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
