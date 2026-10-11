import json
import sys
import threading
import xml.etree.ElementTree as ET

import pytest

from pycrux.logging import (
    MDC,
    FormatterFactory,
    JsonFormatter,
    LogConfig,
    LogConfigParser,
    LogFormat,
    LogLevel,
    LogManager,
    OutputConfig,
    TextFormatter,
    XmlFormatter,
)

NAME = "pycrux_logging_test"


@pytest.fixture(autouse=True)
def _clean():
    MDC.clear()
    yield
    LogManager.shutdown()
    MDC.clear()


def _read(path):
    return path.read_text(encoding="utf-8")


def _failing():
    try:
        try:
            raise KeyError("db row missing")
        except KeyError as exc:
            raise ValueError("cannot load order") from exc
    except ValueError as exc:
        raise RuntimeError("request failed") from exc


# --- MDC -------------------------------------------------------------------


def test_mdc_put_get_remove_clear() -> None:
    MDC.put("userId", "42")
    MDC.put("requestId", "r1")
    assert MDC.get("userId") == "42"
    assert MDC.get("missing") is None
    assert MDC.get("missing", "dflt") == "dflt"

    MDC.remove("userId")
    MDC.remove("userId")  # no error when absent
    assert MDC.get_all() == {"requestId": "r1"}

    MDC.clear()
    assert MDC.get_all() == {}


def test_mdc_get_all_is_a_copy() -> None:
    MDC.put("a", 1)
    MDC.get_all()["a"] = 2
    assert MDC.get("a") == 1


def test_mdc_scope_restores_previous_values() -> None:
    MDC.put("a", 1)
    with MDC.scope(a=2, b=3):
        assert MDC.get_all() == {"a": 2, "b": 3}
    assert MDC.get_all() == {"a": 1}


def test_mdc_scope_restores_on_exception_and_is_reentrant() -> None:
    MDC.put("a", 1)
    scope = MDC.scope(a=2)
    with pytest.raises(RuntimeError):
        with scope:
            with scope:
                assert MDC.get("a") == 2
            assert MDC.get("a") == 2
            raise RuntimeError("boom")
    assert MDC.get_all() == {"a": 1}


def test_request_scope_generates_request_id() -> None:
    with MDC.request_scope(userId="7") as rid:
        assert rid
        assert MDC.get("requestId") == rid
        assert MDC.get("userId") == "7"
    assert MDC.get_all() == {}

    with MDC.request_scope("fixed") as rid:
        assert rid == "fixed"


def test_mdc_is_isolated_per_thread() -> None:
    MDC.put("requestId", "main")
    seen = {}

    def worker() -> None:
        seen["before"] = MDC.get_all()
        MDC.put("requestId", "worker")
        seen["after"] = MDC.get("requestId")

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()

    assert seen == {"before": {}, "after": "worker"}
    assert MDC.get("requestId") == "main"


# --- Config parsing --------------------------------------------------------


def test_parse_level() -> None:
    assert LogConfigParser.parse_level("warn") == 30
    assert LogConfigParser.parse_level("WARN") == 30
    assert LogConfigParser.parse_level(LogLevel.ERROR) == 40
    for alias in ("WARNING", "FATAL"):
        with pytest.raises(ValueError):
            LogConfigParser.parse_level(alias)
    assert LogConfigParser.parse_level(10) == 10
    assert LogConfigParser.parse_level("15") == 15
    with pytest.raises(ValueError):
        LogConfigParser.parse_level("loud")


def test_log_level_enum() -> None:
    assert LogLevel.from_string("warn") is LogLevel.WARN
    assert LogLevel.from_string(LogLevel.INFO) is LogLevel.INFO
    assert LogLevel.WARN == 30
    assert LogLevel.names() == ["CRITICAL", "ERROR", "WARN", "INFO", "DEBUG", "NOTSET"]
    with pytest.raises(ValueError):
        LogLevel.from_string("loud")
    with pytest.raises(ValueError):
        LogLevel.from_string("")


def test_parse_config_from_dict_and_extension_inference() -> None:
    cfg = LogConfigParser.parse(
        {
            "level": "debug",
            "levels": {"urllib3": "warn"},
            "outputs": [{"path": "logs/app.json"}, {"format": "txt"}],
            "mdc_keys": "requestId, userId",
        }
    )
    assert cfg.level == 10
    assert cfg.levels == {"urllib3": 30}
    assert cfg.outputs[0].format is LogFormat.JSON
    assert cfg.outputs[0].target.value == "file"
    assert cfg.outputs[1].format is LogFormat.TEXT
    assert cfg.mdc_keys == ("requestId", "userId")


def test_parse_config_from_json_file(tmp_path) -> None:
    config_file = tmp_path / "logging.json"
    config_file.write_text(json.dumps({"level": "ERROR", "outputs": [{"format": "xml"}]}))
    cfg = LogConfigParser.parse(config_file)
    assert cfg.level == 40
    assert cfg.outputs[0].format is LogFormat.XML


def test_parse_config_env_overrides() -> None:
    cfg = LogConfigParser.parse(
        {"level": "INFO"},
        env={
            "PYCRUX_LOG_LEVEL": "debug",
            "PYCRUX_LOG_FILE": "out/app.xml",
            "PYCRUX_LOG_MDC_KEYS": "requestId",
            "PYCRUX_LOG_CAPTURE_UNCAUGHT": "true",
        },
    )
    assert cfg.level == 10
    assert cfg.outputs[0].format is LogFormat.XML
    assert cfg.mdc_keys == ("requestId",)
    assert cfg.capture_uncaught is True


@pytest.mark.parametrize(
    "bad",
    [
        {"unknown": 1},
        {"outputs": [{"bogus": 1}]},
        {"outputs": [{"target": "file"}]},
        {"outputs": []},
        {"level": "loud"},
    ],
)
def test_parse_config_rejects_invalid(bad) -> None:
    with pytest.raises(ValueError):
        LogConfigParser.parse(bad)


def test_parse_config_rejects_unsupported_file(tmp_path) -> None:
    with pytest.raises(ValueError):
        LogConfigParser.parse(tmp_path / "logging.ini")


def test_invalid_text_pattern_is_rejected() -> None:
    with pytest.raises(ValueError):
        TextFormatter("{nope}")


def test_formatter_factory_creates_formatter_per_format() -> None:
    assert isinstance(FormatterFactory.create("json"), JsonFormatter)
    assert isinstance(FormatterFactory.create(".xml"), XmlFormatter)
    assert isinstance(FormatterFactory.create(LogFormat.TEXT, pattern="{message}"), TextFormatter)
    with pytest.raises(ValueError):
        FormatterFactory.create("yaml")


# --- Output formats --------------------------------------------------------


def test_text_output_with_mdc_and_extension(tmp_path) -> None:
    LogManager.configure({"outputs": [{"format": "text", "path": str(tmp_path / "app")}]}, name=NAME)
    with MDC.request_scope("req-1", userId="42"):
        LogManager.get_logger(NAME).info("hello %s", "world")

    content = _read(tmp_path / "app.txt")
    assert "INFO" in content
    assert "hello world" in content
    assert "requestId=req-1" in content
    assert "userId=42" in content


def test_text_pattern_can_pick_single_mdc_key(tmp_path) -> None:
    LogManager.configure(
        {
            "outputs": [
                {
                    "path": str(tmp_path / "p.txt"),
                    "pattern": "{level}|{mdc[requestId]}|{message}",
                }
            ]
        },
        name=NAME,
    )
    with MDC.request_scope("abc"):
        LogManager.get_logger(NAME).warning("careful")
    assert _read(tmp_path / "p.txt").strip() == "WARNING|abc|careful"


def test_json_output_is_one_object_per_line(tmp_path) -> None:
    LogManager.configure({"outputs": [{"format": "json", "path": str(tmp_path / "app")}]}, name=NAME)
    log = LogManager.get_logger(NAME)
    with MDC.request_scope("r9", userId="u1"):
        log.info("first", extra={"orderId": 5})
        log.info("second")

    lines = _read(tmp_path / "app.json").splitlines()
    first, second = (json.loads(line) for line in lines)
    assert first["message"] == "first"
    assert first["level"] == "INFO"
    assert first["mdc"] == {"requestId": "r9", "userId": "u1"}
    assert first["extra"] == {"orderId": 5}
    assert first["source"]["function"] == "test_json_output_is_one_object_per_line"
    assert second["message"] == "second"


def test_xml_output_is_well_formed(tmp_path) -> None:
    LogManager.configure({"outputs": [{"format": "xml", "path": str(tmp_path / "app")}]}, name=NAME)
    with MDC.request_scope("x1"):
        LogManager.get_logger(NAME).error("bad <input> & \x00 stuff")

    root = ET.fromstring("<log>" + _read(tmp_path / "app.xml") + "</log>")
    event = root.find("event")
    assert event is not None
    assert event.get("level") == "ERROR"
    assert "<input> &" in event.findtext("message")
    entry = event.find("mdc/entry")
    assert entry.get("key") == "requestId"
    assert entry.text == "x1"


def test_multiple_outputs_receive_every_event(tmp_path) -> None:
    LogManager.configure(
        {
            "outputs": [
                {"format": "json", "path": str(tmp_path / "a")},
                {"format": "xml", "path": str(tmp_path / "b")},
                {"format": "text", "path": str(tmp_path / "c")},
            ]
        },
        name=NAME,
    )
    LogManager.get_logger(NAME).info("everywhere")
    for filename in ("a.json", "b.xml", "c.txt"):
        assert "everywhere" in _read(tmp_path / filename)


def test_output_level_filters_independently(tmp_path) -> None:
    LogManager.configure(
        {
            "level": "DEBUG",
            "outputs": [
                {"path": str(tmp_path / "all.txt")},
                {"path": str(tmp_path / "errors.txt"), "level": "ERROR"},
            ],
        },
        name=NAME,
    )
    log = LogManager.get_logger(NAME)
    log.debug("noise")
    log.error("boom")

    assert "noise" in _read(tmp_path / "all.txt")
    errors = _read(tmp_path / "errors.txt")
    assert "boom" in errors
    assert "noise" not in errors


def test_console_output(capsys) -> None:
    LogManager.configure({"outputs": [{"format": "json", "stream": "stdout"}]}, name=NAME)
    LogManager.get_logger(NAME).info("to console")
    assert json.loads(capsys.readouterr().out)["message"] == "to console"


# --- Exceptions ------------------------------------------------------------


def test_json_captures_full_stack_and_cause_chain(tmp_path) -> None:
    LogManager.configure({"outputs": [{"format": "json", "path": str(tmp_path / "app")}]}, name=NAME)
    with MDC.request_scope("flow-1"):
        try:
            _failing()
        except RuntimeError:
            LogManager.get_logger(NAME).exception("Order failed")

    record = json.loads(_read(tmp_path / "app.json"))
    exc = record["exception"]
    assert exc["type"] == "RuntimeError"
    assert exc["message"] == "request failed"
    assert "Traceback (most recent call last)" in exc["stack_trace"]
    assert "KeyError: 'db row missing'" in exc["stack_trace"]
    assert [c["type"] for c in exc["causes"]] == ["ValueError", "KeyError"]
    assert all(c["relation"] == "cause" for c in exc["causes"])
    assert exc["frames"][-1]["function"] == "_failing"
    assert record["mdc"]["requestId"] == "flow-1"


def test_text_shows_stack_and_root_cause(tmp_path) -> None:
    LogManager.configure({"outputs": [{"path": str(tmp_path / "app.txt")}]}, name=NAME)
    try:
        _failing()
    except RuntimeError:
        LogManager.get_logger(NAME).exception("Order failed")

    content = _read(tmp_path / "app.txt")
    assert "Traceback (most recent call last)" in content
    assert "direct cause" in content
    assert "Root cause: KeyError: 'db row missing'" in content


def test_xml_contains_exception_details(tmp_path) -> None:
    LogManager.configure({"outputs": [{"format": "xml", "path": str(tmp_path / "app.xml")}]}, name=NAME)
    try:
        _failing()
    except RuntimeError:
        LogManager.get_logger(NAME).exception("Order failed")

    root = ET.fromstring("<log>" + _read(tmp_path / "app.xml") + "</log>")
    exc = root.find("event/exception")
    assert exc.get("type") == "RuntimeError"
    assert "Traceback" in exc.findtext("stackTrace")
    assert [c.get("type") for c in exc.findall("causes/cause")] == ["ValueError", "KeyError"]
    assert exc.find("frames/frame").get("file")


def test_stack_trace_can_be_disabled(tmp_path) -> None:
    LogManager.configure(
        {"include_stack_trace": False, "outputs": [{"format": "json", "path": str(tmp_path / "a.json")}]},
        name=NAME,
    )
    try:
        _failing()
    except RuntimeError:
        LogManager.get_logger(NAME).exception("Order failed")

    exc = json.loads(_read(tmp_path / "a.json"))["exception"]
    assert exc["type"] == "RuntimeError"
    assert "stack_trace" not in exc
    assert "frames" not in exc


def test_uncaught_exceptions_are_logged(tmp_path) -> None:
    original = sys.excepthook
    LogManager.configure(
        {"capture_uncaught": True, "outputs": [{"format": "json", "path": str(tmp_path / "a.json")}]},
        name=NAME,
    )
    try:
        _failing()
    except RuntimeError:
        sys.excepthook(*sys.exc_info())

    record = json.loads(_read(tmp_path / "a.json"))
    assert record["level"] == "CRITICAL"
    assert record["exception"]["type"] == "RuntimeError"

    LogManager.shutdown()
    assert sys.excepthook is original


# --- Configurable context --------------------------------------------------


def test_mdc_keys_allow_list_and_defaults(tmp_path) -> None:
    LogManager.configure(
        {
            "mdc_keys": ["app", "requestId"],
            "mdc_defaults": {"app": "orders"},
            "outputs": [{"format": "json", "path": str(tmp_path / "a.json")}],
        },
        name=NAME,
    )
    with MDC.request_scope("r5", password="secret"):
        LogManager.get_logger(NAME).info("scoped")

    assert json.loads(_read(tmp_path / "a.json"))["mdc"] == {"app": "orders", "requestId": "r5"}


def test_mdc_value_overrides_default(tmp_path) -> None:
    LogManager.configure(
        {"mdc_defaults": {"env": "dev"}, "outputs": [{"format": "json", "path": str(tmp_path / "a.json")}]},
        name=NAME,
    )
    with MDC.scope(env="prod"):
        LogManager.get_logger(NAME).info("x")
    assert json.loads(_read(tmp_path / "a.json"))["mdc"]["env"] == "prod"


# --- LogManager.configure() lifecycle -------------------------------------------------


def test_configure_twice_does_not_duplicate_output(tmp_path) -> None:
    config = {"outputs": [{"path": str(tmp_path / "a.txt"), "pattern": "{message}"}]}
    LogManager.configure(config, name=NAME)
    LogManager.configure(config, name=NAME)
    LogManager.get_logger(NAME).info("once")
    assert _read(tmp_path / "a.txt").splitlines() == ["once"]


def test_configure_accepts_logconfig_object(tmp_path) -> None:
    cfg = LogConfig(outputs=[OutputConfig(format="json", target="file", path=str(tmp_path / "x"))])
    LogManager.configure(cfg, name=NAME)
    LogManager.get_logger(NAME).info("obj")
    assert json.loads(_read(tmp_path / "x.json"))["message"] == "obj"
