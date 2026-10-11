"""Tests for ``pycrux.io.base`` — ``TextUtils``, ``FileUtils``, ``PlatformUtils``, ``SymbolUtils``."""

import ctypes
import gzip
import hashlib
import io
import os
import subprocess
import tarfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

import pycrux.io.base as base
from pycrux.io.base import (
    DotnetVersion,
    FileUtils,
    InvalidTextLocationError,
    PathUtils,
    PlatformId,
    PlatformUtils,
    SymbolUtils,
    TextUtils,
)
from pycrux.io.paths import PathUtils as PathsPathUtils

from .conftest import _stubs

SolidLSPException = base.SolidLSPException

# --- TextUtils -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("index", "expected"),
    [(0, (0, 0)), (1, (0, 1)), (2, (0, 2)), (3, (1, 0)), (4, (1, 1)), (5, (1, 2))],
)
def test_get_line_col_from_index(index: int, expected: tuple[int, int]) -> None:
    assert TextUtils.get_line_col_from_index("ab\ncd", index) == expected


@pytest.mark.parametrize(
    ("line", "col", "expected"),
    [(0, 0, 0), (0, 1, 1), (0, 2, 2), (1, 0, 3), (1, 1, 4), (1, 2, 5)],
)
def test_get_index_from_line_col(line: int, col: int, expected: int) -> None:
    assert TextUtils.get_index_from_line_col("ab\ncd", line, col) == expected


def test_index_and_line_col_are_inverse() -> None:
    text = "first\nsecond line\n\nlast"
    for index in range(len(text)):
        line, col = TextUtils.get_line_col_from_index(text, index)
        assert TextUtils.get_index_from_line_col(text, line, col) == index


def test_get_index_from_line_col_beyond_the_text_raises() -> None:
    with pytest.raises(InvalidTextLocationError):
        TextUtils.get_index_from_line_col("ab\ncd", 2, 0)
    assert issubclass(InvalidTextLocationError, Exception)


@pytest.mark.parametrize(
    ("line", "col", "inserted", "expected"),
    [(0, 0, "abc", (0, 3)), (4, 2, "x", (4, 3)), (1, 5, "a\nb", (2, 1)), (0, 0, "\n", (1, 0)), (2, 3, "a\nb\nc", (4, 1)), (0, 0, "", (0, 0))],
)
def test_updated_position_after_edit(line: int, col: int, inserted: str, expected: tuple[int, int]) -> None:
    assert TextUtils._get_updated_position_from_line_and_column_and_edit(line, col, inserted) == expected


def test_delete_text_between_positions() -> None:
    assert TextUtils.delete_text_between_positions("hello\nworld", 0, 2, 1, 2) == ("herld", "llo\nwo")
    assert TextUtils.delete_text_between_positions("abc", 0, 1, 0, 2) == ("ac", "b")
    assert TextUtils.delete_text_between_positions("abc", 0, 1, 0, 1) == ("abc", "")


def test_insert_text_at_position() -> None:
    assert TextUtils.insert_text_at_position("ab\ncd", 0, 1, "ZZ") == ("aZZb\ncd", 0, 3)
    assert TextUtils.insert_text_at_position("ab\ncd", 1, 2, "!") == ("ab\ncd!", 1, 3)
    assert TextUtils.insert_text_at_position("ab\ncd", 0, 0, "x\ny") == ("x\nyab\ncd", 1, 1)


def test_insert_text_after_the_last_line_adds_the_missing_newline() -> None:
    new_text, line, col = TextUtils.insert_text_at_position("a\nb", 2, 0, "c")
    assert new_text == "a\nb\nc"
    assert (line, col) == (2, 1)  # regression: the helper newline used to push the cursor one line too far


def test_insert_multiline_text_after_the_last_line() -> None:
    assert TextUtils.insert_text_at_position("a\nb", 2, 0, "x\ny") == ("a\nb\nx\ny", 3, 1)


def test_insert_text_far_beyond_the_text_raises() -> None:
    with pytest.raises(InvalidTextLocationError):
        TextUtils.insert_text_at_position("a\nb", 5, 0, "c")
    with pytest.raises(InvalidTextLocationError):
        TextUtils.insert_text_at_position("a\nb", 2, 3, "c")


def test_insert_then_delete_round_trip() -> None:
    text = "line one\nline two"
    inserted, line, col = TextUtils.insert_text_at_position(text, 1, 5, "INSERTED ")
    restored, deleted = TextUtils.delete_text_between_positions(inserted, 1, 5, line, col)
    assert (restored, deleted) == (text, "INSERTED ")


# --- FileUtils.read_file -----------------------------------------------------------------------


def test_read_file(tmp_path) -> None:
    path = tmp_path / "a.txt"
    path.write_text("héllo", encoding="utf-8")
    assert FileUtils.read_file(str(path), "utf-8") == "héllo"


def test_read_file_missing_raises_file_not_found(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        FileUtils.read_file(str(tmp_path / "missing.txt"), "utf-8")


def test_read_file_falls_back_to_a_detected_encoding(tmp_path) -> None:
    path = tmp_path / "latin.txt"
    path.write_bytes("Voilà un café très crémeux, déjà vu à Noël".encode("latin-1"))
    assert FileUtils.read_file(str(path), "utf-8") == "Voilà un café très crémeux, déjà vu à Noël"


def test_read_file_reraises_when_no_encoding_matches(tmp_path, monkeypatch) -> None:
    path = tmp_path / "bad.bin"
    path.write_bytes(b"\xff\xfe\xfa\xfb")
    monkeypatch.setattr(base.charset_normalizer, "from_path", lambda _p: SimpleNamespace(best=lambda: None))
    with pytest.raises(UnicodeDecodeError):
        FileUtils.read_file(str(path), "utf-8")


def test_read_file_unknown_encoding_name_raises(tmp_path) -> None:
    path = tmp_path / "a.txt"
    path.write_text("x", encoding="utf-8")
    with pytest.raises(LookupError):
        FileUtils.read_file(str(path), "no-such-encoding")


# --- FileUtils checksum / validation helpers ------------------------------------------------------


def test_calculate_sha256(tmp_path) -> None:
    path = tmp_path / "abc.bin"
    path.write_bytes(b"abc")
    assert FileUtils.calculate_sha256(str(path)) == hashlib.sha256(b"abc").hexdigest()
    assert FileUtils.calculate_sha256(str(path)).startswith("ba7816bf")


def test_calculate_sha256_large_file_is_chunked(tmp_path) -> None:
    path = tmp_path / "big.bin"
    data = os.urandom(100_000)
    path.write_bytes(data)
    assert FileUtils.calculate_sha256(str(path)) == hashlib.sha256(data).hexdigest()


def test_verify_sha256_if_configured(tmp_path) -> None:
    path = tmp_path / "f.bin"
    path.write_bytes(b"abc")
    digest = hashlib.sha256(b"abc").hexdigest()
    FileUtils._verify_sha256_if_configured(str(path), None)
    FileUtils._verify_sha256_if_configured(str(path), digest)
    FileUtils._verify_sha256_if_configured(str(path), digest.upper())
    with pytest.raises(SolidLSPException, match="Checksum verification failed"):
        FileUtils._verify_sha256_if_configured(str(path), "0" * 64)


def test_validate_download_host() -> None:
    FileUtils._validate_download_host("https://example.com/x", None)
    FileUtils._validate_download_host("https://example.com/x", [])
    FileUtils._validate_download_host("https://Example.COM/x", ("example.com",))
    FileUtils._validate_download_host("https://example.com/x", ["EXAMPLE.com", "other.org"])


@pytest.mark.parametrize("url", ["https://evil.test/x", "not-a-url", "file:///etc/passwd"])
def test_validate_download_host_rejects_other_hosts(url: str) -> None:
    with pytest.raises(SolidLSPException, match="Refusing to download from host"):
        FileUtils._validate_download_host(url, ("example.com",))


def test_validate_download_host_reports_unknown_host() -> None:
    with pytest.raises(SolidLSPException, match="<unknown>"):
        FileUtils._validate_download_host("no-host", ["example.com"])


def test_validate_extraction_path(tmp_path) -> None:
    root = str(tmp_path / "out")
    assert FileUtils._validate_extraction_path("a/b.txt", root) == os.path.abspath(os.path.join(root, "a", "b.txt"))
    assert FileUtils._validate_extraction_path("dir/", root).endswith("dir")
    assert FileUtils._validate_extraction_path(".", root) == os.path.abspath(root)


@pytest.mark.parametrize("member", ["../evil.txt", "a/../../evil.txt", "..", "/etc/passwd"])
def test_validate_extraction_path_rejects_traversal(tmp_path, member: str) -> None:
    with pytest.raises(SolidLSPException, match="Unsafe archive member"):
        FileUtils._validate_extraction_path(member, str(tmp_path / "out"))


# --- archive extraction -----------------------------------------------------------------------------


def _make_zip(path: Path, members: dict[str, bytes], *, executable: str | None = None, directory: str | None = None) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        if directory:
            archive.writestr(zipfile.ZipInfo(directory.rstrip("/") + "/"), b"")
        for name, data in members.items():
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = (0o755 if name == executable else 0o644) << 16
            archive.writestr(info, data)


def _make_tar(path: Path, members: dict[str, bytes], mode: str) -> None:
    with tarfile.open(path, mode) as archive:  # type: ignore[call-overload]
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def test_extract_zip_archive(tmp_path) -> None:
    archive, target = tmp_path / "a.zip", tmp_path / "out"
    _make_zip(archive, {"top.txt": b"1", "nested/deep/run.sh": b"#!/bin/sh"}, executable="nested/deep/run.sh", directory="emptydir")
    target.mkdir()

    FileUtils._extract_zip_archive(str(archive), str(target))

    assert (target / "top.txt").read_bytes() == b"1"
    assert (target / "nested" / "deep" / "run.sh").read_bytes() == b"#!/bin/sh"
    assert (target / "emptydir").is_dir()
    if os.name != "nt":
        assert (target / "nested" / "deep" / "run.sh").stat().st_mode & 0o777 == 0o755


def test_extract_zip_archive_rejects_path_traversal(tmp_path) -> None:
    archive, target = tmp_path / "evil.zip", tmp_path / "out"
    _make_zip(archive, {"../escaped.txt": b"x"})
    target.mkdir()
    with pytest.raises(SolidLSPException, match="Unsafe archive member"):
        FileUtils._extract_zip_archive(str(archive), str(target))
    assert not (tmp_path / "escaped.txt").exists()


@pytest.mark.parametrize(("archive_type", "mode"), [("tar", "w:"), ("gztar", "w:gz"), ("bztar", "w:bz2"), ("xztar", "w:xz")])
def test_extract_tar_archive(tmp_path, archive_type: str, mode: str) -> None:
    archive, target = tmp_path / "a.tar", tmp_path / "out"
    _make_tar(archive, {"x/y.txt": b"data", "z.txt": b"zz"}, mode)
    target.mkdir()

    FileUtils._extract_tar_archive(str(archive), str(target), archive_type)

    assert (target / "x" / "y.txt").read_bytes() == b"data"
    assert (target / "z.txt").read_bytes() == b"zz"


def test_extract_tar_archive_rejects_traversal_before_extracting_anything(tmp_path) -> None:
    archive, target = tmp_path / "evil.tar", tmp_path / "out"
    _make_tar(archive, {"good.txt": b"ok", "../evil.txt": b"x"}, "w:")
    target.mkdir()
    with pytest.raises(SolidLSPException, match="Unsafe archive member"):
        FileUtils._extract_tar_archive(str(archive), str(target), "tar")
    assert not (target / "good.txt").exists()
    assert not (tmp_path / "evil.txt").exists()


# --- downloads -----------------------------------------------------------------------------------------


class FakeResponse:
    def __init__(self, content: bytes = b"payload", status: int = 200, url: str = "https://example.com/file") -> None:
        self._content = content
        self.status_code = status
        self.text = "error body"
        self.url = url
        self.closed = False

    def iter_content(self, chunk_size: int = 1):
        for start in range(0, len(self._content), 4):
            yield self._content[start : start + 4]
        yield b""  # empty chunks are skipped

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_get(monkeypatch):
    state = SimpleNamespace(response=FakeResponse(), calls=[])

    def get(url, stream=False, timeout=None):
        state.calls.append((url, stream, timeout))
        return state.response

    monkeypatch.setattr(base.requests, "get", get)
    return state


def test_download_file_verified_writes_the_target(fake_get, tmp_path) -> None:
    target = tmp_path / "sub" / "file.bin"
    FileUtils.download_file_verified("https://example.com/file", str(target))

    assert target.read_bytes() == b"payload"
    assert fake_get.calls == [("https://example.com/file", True, 60)]
    assert fake_get.response.closed is True
    assert [p.name for p in target.parent.iterdir()] == ["file.bin"]  # temp file is gone


def test_download_file_verified_accepts_matching_checksum_and_hosts(fake_get, tmp_path) -> None:
    target = tmp_path / "file.bin"
    FileUtils.download_file_verified(
        "https://example.com/file",
        str(target),
        expected_sha256=hashlib.sha256(b"payload").hexdigest(),
        allowed_hosts=["example.com"],
    )
    assert target.read_bytes() == b"payload"


def test_download_file_verified_rejects_a_checksum_mismatch(fake_get, tmp_path) -> None:
    target = tmp_path / "file.bin"
    with pytest.raises(SolidLSPException, match="Error downloading file"):
        FileUtils.download_file_verified("https://example.com/file", str(target), expected_sha256="0" * 64)
    assert not target.exists()
    assert list(tmp_path.iterdir()) == []  # no temp file left behind
    assert fake_get.response.closed is True


def test_download_file_verified_rejects_http_errors(fake_get, tmp_path) -> None:
    fake_get.response = FakeResponse(status=404)
    with pytest.raises(SolidLSPException, match="Error downloading file"):
        FileUtils.download_file_verified("https://example.com/file", str(tmp_path / "f"))
    assert not (tmp_path / "f").exists()


def test_download_file_verified_rejects_a_disallowed_host_before_connecting(fake_get, tmp_path) -> None:
    with pytest.raises(SolidLSPException, match="Refusing to download"):
        FileUtils.download_file_verified("https://evil.test/file", str(tmp_path / "f"), allowed_hosts=["example.com"])
    assert fake_get.calls == []


def test_download_file_verified_rejects_redirects_to_other_hosts(fake_get, tmp_path) -> None:
    fake_get.response = FakeResponse(url="https://evil.test/file")
    with pytest.raises(SolidLSPException, match="Error downloading file"):
        FileUtils.download_file_verified("https://example.com/file", str(tmp_path / "f"), allowed_hosts=["example.com"])
    assert list(tmp_path.iterdir()) == []


def test_download_file_verified_wraps_network_errors(monkeypatch, tmp_path) -> None:
    def boom(*_a, **_k):
        raise ConnectionError("offline")

    monkeypatch.setattr(base.requests, "get", boom)
    with pytest.raises(SolidLSPException, match="Error downloading file"):
        FileUtils.download_file_verified("https://example.com/file", str(tmp_path / "f"))


def test_download_file_delegates_to_the_verified_variant(monkeypatch) -> None:
    calls: list[tuple] = []
    monkeypatch.setattr(FileUtils, "download_file_verified", staticmethod(lambda *a, **k: calls.append((a, k))))
    FileUtils.download_file("https://example.com/f", "/tmp/target")
    assert calls == [(("https://example.com/f", "/tmp/target"), {})]


# --- download_and_extract_archive(_verified) -------------------------------------------------------------


@pytest.fixture
def serve_archive(monkeypatch, tmp_path):
    """Make ``download_file_verified`` copy a prepared file instead of using the network."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    state = SimpleNamespace(source=None, calls=[], fail=False)

    def fake_download(url, target_path, expected_sha256=None, allowed_hosts=None):
        state.calls.append((url, expected_sha256, allowed_hosts))
        if state.fail:
            raise SolidLSPException("Error downloading file.")
        Path(target_path).write_bytes(Path(state.source).read_bytes())

    monkeypatch.setattr(FileUtils, "download_file_verified", staticmethod(fake_download))
    state.home = home
    return state


@pytest.mark.parametrize(("archive_type", "mode"), [("tar", "w:"), ("gztar", "w:gz"), ("bztar", "w:bz2"), ("xztar", "w:xz")])
def test_download_and_extract_tar_variants(serve_archive, tmp_path, archive_type: str, mode: str) -> None:
    serve_archive.source = tmp_path / "src.tar"
    _make_tar(serve_archive.source, {"bin/tool": b"exe"}, mode)
    target = tmp_path / "out"

    FileUtils.download_and_extract_archive("https://example.com/a", str(target), archive_type)

    assert (target / "bin" / "tool").read_bytes() == b"exe"
    assert list((serve_archive.home / "solidlsp_tmp").iterdir()) == []


def test_download_and_extract_zip(serve_archive, tmp_path) -> None:
    serve_archive.source = tmp_path / "src.zip"
    _make_zip(serve_archive.source, {"a.txt": b"A"})
    target = tmp_path / "out"
    FileUtils.download_and_extract_archive("https://example.com/a", str(target), "zip")
    assert (target / "a.txt").read_bytes() == b"A"


def test_download_and_extract_zip_gz(serve_archive, tmp_path) -> None:
    inner = tmp_path / "inner.zip"
    _make_zip(inner, {"a.txt": b"A"})
    serve_archive.source = tmp_path / "src.zip.gz"
    serve_archive.source.write_bytes(gzip.compress(inner.read_bytes()))
    target = tmp_path / "out"

    FileUtils.download_and_extract_archive("https://example.com/a", str(target), "zip.gz")

    assert (target / "a.txt").read_bytes() == b"A"
    assert list((serve_archive.home / "solidlsp_tmp").iterdir()) == []


def test_download_and_extract_gz_writes_a_single_file(serve_archive, tmp_path) -> None:
    serve_archive.source = tmp_path / "src.gz"
    serve_archive.source.write_bytes(gzip.compress(b"plain content"))
    target = tmp_path / "nested" / "tool"

    FileUtils.download_and_extract_archive("https://example.com/a", str(target), "gz")

    assert target.read_bytes() == b"plain content"
    assert [p.name for p in target.parent.iterdir()] == ["tool"]


def test_download_and_extract_binary_moves_the_download(serve_archive, tmp_path) -> None:
    serve_archive.source = tmp_path / "src.bin"
    serve_archive.source.write_bytes(b"\x7fELF")
    target = tmp_path / "bin" / "tool"

    FileUtils.download_and_extract_archive("https://example.com/a", str(target), "binary")

    assert target.read_bytes() == b"\x7fELF"
    assert list((serve_archive.home / "solidlsp_tmp").iterdir()) == []


def test_download_and_extract_unknown_archive_type(serve_archive, tmp_path) -> None:
    serve_archive.source = tmp_path / "src.bin"
    serve_archive.source.write_bytes(b"x")
    with pytest.raises(SolidLSPException, match="Error extracting archive"):
        FileUtils.download_and_extract_archive("https://example.com/a", str(tmp_path / "out"), "rar")
    assert list((serve_archive.home / "solidlsp_tmp").iterdir()) == []


def test_download_and_extract_wraps_download_failures(serve_archive, tmp_path) -> None:
    serve_archive.fail = True
    with pytest.raises(SolidLSPException, match="Error extracting archive"):
        FileUtils.download_and_extract_archive("https://example.com/a", str(tmp_path / "out"), "zip")


def test_download_and_extract_rejects_unsafe_members(serve_archive, tmp_path) -> None:
    serve_archive.source = tmp_path / "evil.zip"
    _make_zip(serve_archive.source, {"../evil.txt": b"x"})
    with pytest.raises(SolidLSPException, match="Error extracting archive"):
        FileUtils.download_and_extract_archive("https://example.com/a", str(tmp_path / "out"), "zip")
    assert not (tmp_path / "evil.txt").exists()


def test_download_and_extract_forwards_verification_options(serve_archive, tmp_path) -> None:
    serve_archive.source = tmp_path / "src.zip"
    _make_zip(serve_archive.source, {"a.txt": b"A"})
    FileUtils.download_and_extract_archive_verified(
        "https://example.com/a", str(tmp_path / "out"), "zip", expected_sha256="abc", allowed_hosts=["example.com"]
    )
    assert serve_archive.calls == [("https://example.com/a", "abc", ["example.com"])]


# --- PlatformId / DotnetVersion --------------------------------------------------------------------------


def test_platform_id_values_and_is_windows() -> None:
    assert PlatformId.OSX_arm64.value == "osx-arm64"
    assert PlatformId("linux-musl-x64") is PlatformId.LINUX_MUSL_x64
    assert [p.is_windows() for p in (PlatformId.WIN_x86, PlatformId.WIN_x64, PlatformId.WIN_arm64)] == [True] * 3
    assert not any(p.is_windows() for p in PlatformId if not p.value.startswith("win"))
    assert isinstance(PlatformId.OSX, str)


def test_dotnet_version_values() -> None:
    assert [v.value for v in DotnetVersion] == ["4", "6", "7", "8", "9", "mono"]


# --- PlatformUtils.get_platform_id -------------------------------------------------------------------------


def _platform(monkeypatch, system: str, machine: str, bitness: str = "64bit", libc: str = "glibc") -> None:
    monkeypatch.setattr(base.platform, "system", lambda: system)
    monkeypatch.setattr(base.platform, "machine", lambda: machine)
    monkeypatch.setattr(base.platform, "architecture", lambda: (bitness, ""))
    monkeypatch.setattr(base.platform, "libc_ver", lambda: (libc, "2.39"))


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        ("Darwin", "arm64", PlatformId.OSX_arm64),
        ("Darwin", "x86_64", PlatformId.OSX_x64),
        ("Linux", "x86_64", PlatformId.LINUX_x64),
        ("Linux", "aarch64", PlatformId.LINUX_arm64),
        ("Linux", "i686", PlatformId.LINUX_x86),
        ("Windows", "AMD64", PlatformId.WIN_x64),
        ("Windows", "ARM64", PlatformId.WIN_arm64),
        ("Windows", "i386", PlatformId.WIN_x86),
    ],
)
def test_get_platform_id(monkeypatch, system: str, machine: str, expected: PlatformId) -> None:
    _platform(monkeypatch, system, machine)
    assert PlatformUtils.get_platform_id() is expected


def test_get_platform_id_detects_musl(monkeypatch) -> None:
    _platform(monkeypatch, "Linux", "x86_64", libc="musl")
    assert PlatformUtils.get_platform_id() is PlatformId.LINUX_MUSL_x64
    _platform(monkeypatch, "Linux", "aarch64", libc="musl")
    assert PlatformUtils.get_platform_id() is PlatformId.LINUX_MUSL_arm64


def test_get_platform_id_ignores_libc_on_32_bit_linux(monkeypatch) -> None:
    _platform(monkeypatch, "Linux", "i686", bitness="32bit", libc="")
    assert PlatformUtils.get_platform_id() is PlatformId.LINUX_x86


def test_get_platform_id_asks_windows_for_an_empty_machine_name(monkeypatch) -> None:
    _platform(monkeypatch, "Windows", "")
    monkeypatch.setattr(PlatformUtils, "_determine_windows_machine_type", staticmethod(lambda: "ARM64"))
    assert PlatformUtils.get_platform_id() is PlatformId.WIN_arm64


@pytest.mark.parametrize(("system", "machine"), [("Plan9", "x86_64"), ("Linux", "riscv64"), ("Darwin", "")])
def test_get_platform_id_rejects_unknown_platforms(monkeypatch, system: str, machine: str) -> None:
    _platform(monkeypatch, system, machine)
    with pytest.raises(SolidLSPException, match="Unknown platform"):
        PlatformUtils.get_platform_id()


# --- PlatformUtils._determine_windows_machine_type ----------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "expected"),
    [(9, "AMD64"), (5, "ARM"), (12, "arm64"), (6, "Intel Itanium-based"), (0, "i386"), (99, "Unknown (99)")],
)
def test_determine_windows_machine_type(monkeypatch, code: int, expected: str) -> None:
    def get_native_system_info(reference) -> None:
        reference._obj.wProcessorArchitecture = code

    fake_windll = SimpleNamespace(kernel32=SimpleNamespace(GetNativeSystemInfo=get_native_system_info))
    monkeypatch.setattr(ctypes, "windll", fake_windll, raising=False)
    assert PlatformUtils._determine_windows_machine_type() == expected


# --- PlatformUtils.get_dotnet_version --------------------------------------------------------------------------


def _dotnet_output(*versions: str) -> bytes:
    return "\n".join(f"Microsoft.NETCore.App {v} [/usr/share/dotnet/shared]" for v in versions).encode() + b"\n"


def _fake_run(monkeypatch, *, dotnet: bytes | Exception, mono: Exception | None = None) -> list[list[str]]:
    calls: list[list[str]] = []

    def run(cmd, capture_output=False, check=False):
        calls.append(cmd)
        outcome = dotnet if cmd[0] == "dotnet" else mono
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(stdout=outcome if outcome is not None else b"")

    monkeypatch.setattr(base.subprocess, "run", run)
    return calls


@pytest.mark.parametrize(
    ("versions", "expected"),
    [
        (["9.0.1"], DotnetVersion.V9),
        (["8.0.4"], DotnetVersion.V8),
        (["7.0.0"], DotnetVersion.V7),
        (["6.0.30"], DotnetVersion.V6),
        (["4.8.1"], DotnetVersion.V4),
        (["6.0.1", "8.0.2"], DotnetVersion.V6),  # the first listed runtime wins
        (["5.0.0", "8.0.2"], DotnetVersion.V8),  # unsupported runtimes are skipped
    ],
)
def test_get_dotnet_version(monkeypatch, versions: list[str], expected: DotnetVersion) -> None:
    calls = _fake_run(monkeypatch, dotnet=_dotnet_output(*versions))
    assert PlatformUtils.get_dotnet_version() is expected
    assert calls == [["dotnet", "--list-runtimes"]]


def test_get_dotnet_version_ignores_other_runtime_lines(monkeypatch) -> None:
    output = b"Microsoft.AspNetCore.App 9.0.0 [/x]\nMicrosoft.NETCore.App 8.0.1 [/x]\n"
    _fake_run(monkeypatch, dotnet=output)
    assert PlatformUtils.get_dotnet_version() is DotnetVersion.V8


def test_get_dotnet_version_without_any_runtime(monkeypatch) -> None:
    _fake_run(monkeypatch, dotnet=b"Microsoft.AspNetCore.App 9.0.0 [/x]\n")
    with pytest.raises(SolidLSPException, match="dotnet not found on the system"):
        PlatformUtils.get_dotnet_version()


def test_get_dotnet_version_with_only_unsupported_runtimes(monkeypatch) -> None:
    _fake_run(monkeypatch, dotnet=_dotnet_output("5.0.17", "3.1.0"))
    with pytest.raises(SolidLSPException, match=r"No supported dotnet version found\. Available versions: 5\.0\.17, 3\.1\.0"):
        PlatformUtils.get_dotnet_version()


@pytest.mark.parametrize("failure", [FileNotFoundError("dotnet"), subprocess.CalledProcessError(1, "dotnet")])
def test_get_dotnet_version_falls_back_to_mono(monkeypatch, failure: Exception) -> None:
    calls = _fake_run(monkeypatch, dotnet=failure, mono=None)
    assert PlatformUtils.get_dotnet_version() is DotnetVersion.VMONO
    assert calls == [["dotnet", "--list-runtimes"], ["mono", "--version"]]


@pytest.mark.parametrize("mono_failure", [FileNotFoundError("mono"), subprocess.CalledProcessError(1, "mono")])
def test_get_dotnet_version_without_dotnet_or_mono(monkeypatch, mono_failure: Exception) -> None:
    _fake_run(monkeypatch, dotnet=FileNotFoundError("dotnet"), mono=mono_failure)
    with pytest.raises(SolidLSPException, match="dotnet or mono not found"):
        PlatformUtils.get_dotnet_version()


# --- SymbolUtils -----------------------------------------------------------------------------------------------


def test_symbol_tree_contains_name() -> None:
    tree = [
        {"name": "Outer", "children": [{"name": "inner_method", "children": []}]},
        {"name": "helper", "children": [{"name": "nested", "children": [{"name": "deep", "children": []}]}]},
    ]
    assert SymbolUtils.symbol_tree_contains_name(tree, "Outer") is True
    assert SymbolUtils.symbol_tree_contains_name(tree, "inner_method") is True
    assert SymbolUtils.symbol_tree_contains_name(tree, "deep") is True
    assert SymbolUtils.symbol_tree_contains_name(tree, "missing") is False
    assert SymbolUtils.symbol_tree_contains_name([], "anything") is False


# --- module wiring ------------------------------------------------------------------------------------------------


def test_path_utils_is_re_exported_from_paths() -> None:
    assert PathUtils is PathsPathUtils


def test_the_stubs_cover_the_third_party_imports() -> None:
    # documents whether this run uses stand-ins or the real packages
    assert isinstance(_stubs.STUBBED, set)
