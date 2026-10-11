"""Tests for ``pycrux.logging.config`` — ``OutputConfig`` and ``LogConfig``."""

import logging
from pathlib import Path

import pytest

from pycrux.logging import LogConfig, LogFormat, LogTarget, OutputConfig

# --- OutputConfig --------------------------------------------------------------


def test_output_defaults() -> None:
    out = OutputConfig()
    assert out.format is LogFormat.TEXT
    assert out.target is LogTarget.CONSOLE
    assert out.path is None
    assert out.level is None
    assert out.stream == "stderr"
    assert out.pattern is None
    assert out.max_bytes == 10 * 1024 * 1024
    assert out.backup_count == 5
    assert out.encoding == "utf-8"


def test_output_coerces_strings() -> None:
    out = OutputConfig(format="JSON", target="File", path="logs/app")
    assert out.format is LogFormat.JSON
    assert out.target is LogTarget.FILE


def test_file_output_requires_path() -> None:
    with pytest.raises(ValueError, match="requires a 'path'"):
        OutputConfig(target="file")
    with pytest.raises(ValueError, match="requires a 'path'"):
        OutputConfig(target="file", path="")


def test_invalid_stream_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid stream"):
        OutputConfig(stream="stdin")
    assert OutputConfig(stream="stdout").stream == "stdout"


@pytest.mark.parametrize("kwargs", [{"max_bytes": -1}, {"backup_count": -1}])
def test_negative_rotation_values_are_rejected(kwargs) -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        OutputConfig(**kwargs)


def test_zero_rotation_values_are_allowed() -> None:
    out = OutputConfig(max_bytes=0, backup_count=0)
    assert (out.max_bytes, out.backup_count) == (0, 0)


def test_invalid_format_or_target_is_rejected() -> None:
    with pytest.raises(ValueError):
        OutputConfig(format="yaml")
    with pytest.raises(ValueError):
        OutputConfig(target="socket")


def test_resolved_path_is_none_for_console() -> None:
    assert OutputConfig().resolved_path() is None
    assert OutputConfig(path="ignored.txt").resolved_path() is None


@pytest.mark.parametrize(
    ("fmt", "expected"),
    [("text", "logs/app.txt"), ("json", "logs/app.json"), ("xml", "logs/app.xml")],
)
def test_resolved_path_adds_format_extension(fmt: str, expected: str) -> None:
    out = OutputConfig(format=fmt, target="file", path="logs/app")
    assert out.resolved_path() == Path(expected)


def test_resolved_path_keeps_existing_suffix() -> None:
    out = OutputConfig(format="json", target="file", path="logs/app.log")
    assert out.resolved_path() == Path("logs/app.log")


def test_resolved_path_expands_user() -> None:
    out = OutputConfig(target="file", path="~/x/app.txt")
    assert out.resolved_path() == Path("~/x/app.txt").expanduser()


# --- LogConfig -----------------------------------------------------------------


def test_log_config_defaults() -> None:
    cfg = LogConfig()
    assert cfg.level == logging.INFO
    assert cfg.levels == {}
    assert len(cfg.outputs) == 1 and cfg.outputs[0].target is LogTarget.CONSOLE
    assert cfg.mdc_keys is None
    assert cfg.mdc_defaults == {}
    assert cfg.include_stack_trace is True
    assert cfg.capture_uncaught is False


def test_log_config_defaults_are_not_shared() -> None:
    first, second = LogConfig(), LogConfig()
    first.levels["x"] = 10
    first.mdc_defaults["a"] = 1
    first.outputs.append(OutputConfig())
    assert second.levels == {} and second.mdc_defaults == {} and len(second.outputs) == 1


def test_log_config_requires_an_output() -> None:
    with pytest.raises(ValueError, match="At least one output"):
        LogConfig(outputs=[])


def test_log_config_normalizes_mdc_keys() -> None:
    assert LogConfig(mdc_keys=["a", "b"]).mdc_keys == ("a", "b")
    assert LogConfig(mdc_keys=[]).mdc_keys is None
    assert LogConfig(mdc_keys=()).mdc_keys is None
    assert LogConfig(mdc_keys=None).mdc_keys is None
