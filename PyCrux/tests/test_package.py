from pycrux import __version__
from pycrux.enums import DeviceType, EnvType, OS, SizeUnit
from pycrux.net import HttpUtils
from pycrux.io import IOUtils


def test_version_is_set() -> None:
    assert __version__


def test_env_type_aliases() -> None:
    assert EnvType.from_string("staging") is EnvType.STAGING
    assert EnvType.STAGING.equals("stg")


def test_size_unit_format() -> None:
    assert SizeUnit.format_bytes(512) == "512 B"
    assert SizeUnit.KB.from_bytes(2048) == 2.0


def test_case_insensitive_enums() -> None:
    assert DeviceType.from_string("mobile") is DeviceType.MOBILE
    assert OS.from_string("macos") is OS.MACOS


def test_io_utils_resolve(tmp_path) -> None:
    IOUtils.set_root(tmp_path)
    assert IOUtils.resolve("data/file.txt") == (tmp_path / "data" / "file.txt").resolve()


def test_http_utils_is_importable() -> None:
    assert HttpUtils is not None
