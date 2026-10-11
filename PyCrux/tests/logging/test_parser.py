"""Tests for ``pycrux.logging.parser.LogConfigParser``."""

import json
import logging

import pytest

from pycrux.logging import LogConfig, LogConfigParser, LogFormat, LogLevel, LogTarget, OutputConfig

# --- parse: sources --------------------------------------------------------------


def test_parse_none_gives_defaults() -> None:
    cfg = LogConfigParser.parse()
    assert cfg == LogConfig()
    assert LogConfigParser.parse(None) == LogConfig()


def test_parse_log_config_is_returned_unchanged() -> None:
    cfg = LogConfig(level=logging.ERROR)
    assert LogConfigParser.parse(cfg) is cfg


def test_parse_log_config_with_env_is_rejected() -> None:
    with pytest.raises(ValueError, match="Environment overrides cannot be applied"):
        LogConfigParser.parse(LogConfig(), env={"PYCRUX_LOG_LEVEL": "debug"})


def test_parse_log_config_with_empty_env_is_allowed() -> None:
    cfg = LogConfig()
    assert LogConfigParser.parse(cfg, env={}) is cfg


def test_parse_mapping_does_not_mutate_input() -> None:
    source = {"level": "debug", "outputs": [{"format": "json"}]}
    LogConfigParser.parse(source)
    assert source == {"level": "debug", "outputs": [{"format": "json"}]}


def test_parse_json_file(tmp_path) -> None:
    path = tmp_path / "logging.json"
    path.write_text(json.dumps({"level": "warn", "mdc_keys": "a,b"}), encoding="utf-8")
    cfg = LogConfigParser.parse(path)
    assert cfg.level == logging.WARNING and cfg.mdc_keys == ("a", "b")
    assert LogConfigParser.parse(str(path)).level == logging.WARNING


def test_parse_rejects_non_json_file(tmp_path) -> None:
    path = tmp_path / "logging.yaml"
    path.write_text("level: debug", encoding="utf-8")
    with pytest.raises(ValueError, match="expected a .json file"):
        LogConfigParser.parse(path)


def test_parse_rejects_json_that_is_not_an_object(tmp_path) -> None:
    path = tmp_path / "logging.json"
    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain a JSON object"):
        LogConfigParser.parse(path)


# --- parse: keys -----------------------------------------------------------------


def test_unknown_config_keys_are_rejected() -> None:
    with pytest.raises(ValueError, match=r"Unknown logging config keys: \['colour'\]"):
        LogConfigParser.parse({"colour": "red"})


def test_levels_mapping() -> None:
    cfg = LogConfigParser.parse({"levels": {"urllib3": "warn", "sql": 15, "x": "20"}})
    assert cfg.levels == {"urllib3": logging.WARNING, "sql": 15, "x": 20}


def test_booleans() -> None:
    cfg = LogConfigParser.parse({"include_stack_trace": "no", "capture_uncaught": "YES"})
    assert cfg.include_stack_trace is False and cfg.capture_uncaught is True
    cfg = LogConfigParser.parse({"include_stack_trace": True, "capture_uncaught": False})
    assert cfg.include_stack_trace is True and cfg.capture_uncaught is False


@pytest.mark.parametrize("bad", ["maybe", 1, None, []])
def test_invalid_booleans_are_rejected(bad) -> None:
    with pytest.raises(ValueError, match="Invalid boolean"):
        LogConfigParser.parse({"capture_uncaught": bad})


def test_mdc_keys_from_string_and_list() -> None:
    assert LogConfigParser.parse({"mdc_keys": " a, b ,, c "}).mdc_keys == ("a", "b", "c")
    assert LogConfigParser.parse({"mdc_keys": ["x", " y "]}).mdc_keys == ("x", "y")
    assert LogConfigParser.parse({"mdc_keys": ""}).mdc_keys is None


def test_mdc_defaults_keys_become_strings() -> None:
    assert LogConfigParser.parse({"mdc_defaults": {1: "a", "b": 2}}).mdc_defaults == {"1": "a", "b": 2}


# --- parse: outputs --------------------------------------------------------------


def test_outputs_must_be_a_list() -> None:
    with pytest.raises(ValueError, match="'outputs' must be a list"):
        LogConfigParser.parse({"outputs": {"format": "json"}})


def test_each_output_must_be_an_object() -> None:
    with pytest.raises(ValueError, match="Each output must be an object"):
        LogConfigParser.parse({"outputs": ["json"]})


def test_unknown_output_keys_are_rejected() -> None:
    with pytest.raises(ValueError, match=r"Unknown output keys: \['colour'\]"):
        LogConfigParser.parse({"outputs": [{"colour": "red"}]})


def test_output_defaults_to_console_without_path() -> None:
    (out,) = LogConfigParser.parse({"outputs": [{}]}).outputs
    assert out.target is LogTarget.CONSOLE and out.format is LogFormat.TEXT


def test_output_target_is_file_when_path_given() -> None:
    (out,) = LogConfigParser.parse({"outputs": [{"path": "logs/app"}]}).outputs
    assert out.target is LogTarget.FILE
    assert out.format is LogFormat.TEXT


@pytest.mark.parametrize(
    ("path", "fmt"),
    [
        ("a.json", LogFormat.JSON),
        ("a.xml", LogFormat.XML),
        ("a.txt", LogFormat.TEXT),
        ("a.log", LogFormat.TEXT),
        ("a.ndjson", LogFormat.JSON),
        ("a.unknown", LogFormat.TEXT),
        ("a", LogFormat.TEXT),
    ],
)
def test_output_format_is_inferred_from_path(path: str, fmt: LogFormat) -> None:
    (out,) = LogConfigParser.parse({"outputs": [{"path": path}]}).outputs
    assert out.format is fmt


def test_explicit_format_wins_over_path_extension() -> None:
    (out,) = LogConfigParser.parse({"outputs": [{"path": "a.json", "format": "xml"}]}).outputs
    assert out.format is LogFormat.XML


def test_output_level_and_other_options() -> None:
    (out,) = LogConfigParser.parse(
        {"outputs": [{"level": "error", "stream": "stdout", "pattern": "{message}", "max_bytes": 5, "backup_count": 1, "encoding": "latin-1"}]}
    ).outputs
    assert out.level == logging.ERROR
    assert (out.stream, out.pattern, out.max_bytes, out.backup_count, out.encoding) == ("stdout", "{message}", 5, 1, "latin-1")


def test_output_level_none_stays_none() -> None:
    (out,) = LogConfigParser.parse({"outputs": [{"level": None}]}).outputs
    assert out.level is None


def test_output_instances_in_a_list_are_accepted_as_mappings_only() -> None:
    with pytest.raises(ValueError):
        LogConfigParser.parse({"outputs": [OutputConfig()]})


# --- parse_level -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (LogLevel.INFO, 20),
        ("warn", 30),
        ("ERROR", 40),
        (15, 15),
        ("15", 15),
        (" 7 ", 7),
        (0, 0),
        (logging.CRITICAL, 50),
    ],
)
def test_parse_level(value, expected: int) -> None:
    assert LogConfigParser.parse_level(value) == expected


@pytest.mark.parametrize("bad", [True, False, "loud", "", None, 1.5])
def test_parse_level_rejects_invalid(bad) -> None:
    with pytest.raises(ValueError):
        LogConfigParser.parse_level(bad)


# --- environment overrides ---------------------------------------------------------


def test_env_prefix_and_keys() -> None:
    assert LogConfigParser.ENV_PREFIX == "PYCRUX_LOG_"
    assert "level" in LogConfigParser.CONFIG_KEYS and "path" in LogConfigParser.OUTPUT_KEYS


def test_env_scalar_overrides() -> None:
    cfg = LogConfigParser.parse(
        {"level": "info"},
        env={
            "PYCRUX_LOG_LEVEL": "debug",
            "PYCRUX_LOG_MDC_KEYS": "requestId, userId",
            "PYCRUX_LOG_STACK_TRACE": "false",
            "PYCRUX_LOG_CAPTURE_UNCAUGHT": "true",
        },
    )
    assert cfg.level == logging.DEBUG
    assert cfg.mdc_keys == ("requestId", "userId")
    assert cfg.include_stack_trace is False
    assert cfg.capture_uncaught is True


def test_env_file_adds_an_output() -> None:
    cfg = LogConfigParser.parse({"outputs": [{}]}, env={"PYCRUX_LOG_FILE": "out/app.xml"})
    assert len(cfg.outputs) == 2
    assert cfg.outputs[1].target is LogTarget.FILE
    assert cfg.outputs[1].format is LogFormat.XML  # inferred from the extension


def test_env_format_applies_to_every_output() -> None:
    cfg = LogConfigParser.parse(
        {"outputs": [{}, {"path": "a.txt"}]}, env={"PYCRUX_LOG_FORMAT": "json"}
    )
    assert [o.format for o in cfg.outputs] == [LogFormat.JSON, LogFormat.JSON]


def test_env_format_without_outputs_creates_a_console_output() -> None:
    cfg = LogConfigParser.parse(None, env={"PYCRUX_LOG_FORMAT": "xml"})
    assert len(cfg.outputs) == 1
    assert cfg.outputs[0].target is LogTarget.CONSOLE and cfg.outputs[0].format is LogFormat.XML


def test_env_file_and_format_combine() -> None:
    cfg = LogConfigParser.parse(None, env={"PYCRUX_LOG_FILE": "a.txt", "PYCRUX_LOG_FORMAT": "json"})
    assert len(cfg.outputs) == 1
    assert cfg.outputs[0].target is LogTarget.FILE and cfg.outputs[0].format is LogFormat.JSON


def test_empty_and_missing_env_values_are_ignored() -> None:
    cfg = LogConfigParser.parse({"level": "warn"}, env={"PYCRUX_LOG_LEVEL": "", "OTHER": "x"})
    assert cfg.level == logging.WARNING


def test_env_does_not_mutate_source_outputs() -> None:
    source = {"outputs": [{"format": "text"}]}
    LogConfigParser.parse(source, env={"PYCRUX_LOG_FORMAT": "json"})
    assert source == {"outputs": [{"format": "text"}]}


def test_invalid_env_value_is_rejected() -> None:
    with pytest.raises(ValueError):
        LogConfigParser.parse(None, env={"PYCRUX_LOG_LEVEL": "loud"})
    with pytest.raises(ValueError, match="Invalid boolean"):
        LogConfigParser.parse(None, env={"PYCRUX_LOG_STACK_TRACE": "perhaps"})
