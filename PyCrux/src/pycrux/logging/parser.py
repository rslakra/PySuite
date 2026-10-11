"""Parse logging configuration from a dict, a JSON file or environment variables.

Example configuration::

    {
      "level": "INFO",
      "levels": {"urllib3": "WARN"},
      "outputs": [
        {"format": "text", "target": "console"},
        {"format": "json", "target": "file", "path": "logs/app"},
        {"format": "xml",  "target": "file", "path": "logs/app.xml", "level": "ERROR"}
      ],
      "mdc_keys": ["requestId", "userId"],
      "mdc_defaults": {"app": "orders"},
      "include_stack_trace": true,
      "capture_uncaught": true
    }

Environment overrides (``LogConfigParser.parse(..., env=os.environ)``):

=============================== ===============================================
``PYCRUX_LOG_LEVEL``              root level
``PYCRUX_LOG_FORMAT``             ``text`` / ``json`` / ``xml`` for every output
``PYCRUX_LOG_FILE``               adds a file output (format inferred from extension)
``PYCRUX_LOG_MDC_KEYS``           comma separated MDC keys to include
``PYCRUX_LOG_STACK_TRACE``        ``true`` / ``false``
``PYCRUX_LOG_CAPTURE_UNCAUGHT``   ``true`` / ``false``
=============================== ===============================================
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar

from .config import LogConfig, OutputConfig
from .types import LogFormat, LogLevel, LogTarget


class LogConfigParser:
    """Builds a :class:`LogConfig` from a mapping, a ``.json`` file or the environment."""

    ENV_PREFIX: ClassVar[str] = "PYCRUX_LOG_"

    CONFIG_KEYS: ClassVar[frozenset[str]] = frozenset(
        {"level", "levels", "outputs", "mdc_keys", "mdc_defaults", "include_stack_trace", "capture_uncaught"}
    )
    OUTPUT_KEYS: ClassVar[frozenset[str]] = frozenset(
        {"format", "target", "path", "level", "stream", "pattern", "max_bytes", "backup_count", "encoding"}
    )

    @classmethod
    def parse(
        cls,
        source: LogConfig | Mapping[str, Any] | str | os.PathLike[str] | None = None,
        *,
        env: Mapping[str, str] | None = None,
    ) -> LogConfig:
        """Build a :class:`LogConfig`.

        Args:
            source: ``None`` (defaults), a ``LogConfig``, a mapping, or the path of
                a ``.json`` file.
            env: Optional environment mapping (usually ``os.environ``) whose
                ``PYCRUX_LOG_*`` values override ``source``.

        Raises:
            ValueError: Unknown keys, invalid values or an unsupported file type.
        """
        if isinstance(source, LogConfig):
            if env:
                raise ValueError("Environment overrides cannot be applied to a LogConfig instance")
            return source

        data = cls._load(source)
        if env:
            data = cls._apply_env(data, env)
        return cls._from_dict(data)

    @classmethod
    def parse_level(cls, value: LogLevel | int | str) -> int:
        """Convert a :class:`LogLevel` name (``"warn"``, ``"ERROR"``) or a number to a numeric level.

        Plain numbers (``15``, ``"15"``) are accepted for custom levels.
        """
        if isinstance(value, bool):
            raise ValueError(f"Invalid log level: {value!r}")
        if isinstance(value, int):
            return int(value)
        if isinstance(value, str) and value.strip().isdigit():
            return int(value)
        return int(LogLevel.from_string(value))

    @staticmethod
    def _load(source: Mapping[str, Any] | str | os.PathLike[str] | None) -> dict[str, Any]:
        if source is None:
            return {}
        if isinstance(source, Mapping):
            return dict(source)
        path = Path(source)
        if path.suffix.lower() != ".json":
            raise ValueError(f"Unsupported logging config file {str(path)!r}; expected a .json file")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Logging config {str(path)!r} must contain a JSON object")
        return data

    @classmethod
    def _from_dict(cls, data: Mapping[str, Any]) -> LogConfig:
        unknown = set(data) - cls.CONFIG_KEYS
        if unknown:
            raise ValueError(f"Unknown logging config keys: {sorted(unknown)}")

        kwargs: dict[str, Any] = {}
        if "level" in data:
            kwargs["level"] = cls.parse_level(data["level"])
        if "levels" in data:
            kwargs["levels"] = {
                str(name): cls.parse_level(level) for name, level in dict(data["levels"]).items()
            }
        if "outputs" in data:
            outputs = data["outputs"]
            if not isinstance(outputs, (list, tuple)):
                raise ValueError("'outputs' must be a list")
            kwargs["outputs"] = [cls._parse_output(item) for item in outputs]
        if "mdc_keys" in data:
            kwargs["mdc_keys"] = cls._parse_keys(data["mdc_keys"])
        if "mdc_defaults" in data:
            kwargs["mdc_defaults"] = {str(k): v for k, v in dict(data["mdc_defaults"]).items()}
        if "include_stack_trace" in data:
            kwargs["include_stack_trace"] = cls._parse_bool(data["include_stack_trace"], "include_stack_trace")
        if "capture_uncaught" in data:
            kwargs["capture_uncaught"] = cls._parse_bool(data["capture_uncaught"], "capture_uncaught")
        return LogConfig(**kwargs)

    @classmethod
    def _parse_output(cls, item: Mapping[str, Any]) -> OutputConfig:
        if not isinstance(item, Mapping):
            raise ValueError(f"Each output must be an object, got {item!r}")
        unknown = set(item) - cls.OUTPUT_KEYS
        if unknown:
            raise ValueError(f"Unknown output keys: {sorted(unknown)}")

        kwargs: dict[str, Any] = dict(item)
        path = kwargs.get("path")
        kwargs["target"] = LogTarget.from_string(kwargs.get("target", "file" if path else "console"))
        if "format" in kwargs:
            kwargs["format"] = LogFormat.from_string(kwargs["format"])
        elif path:
            kwargs["format"] = cls._format_from_path(str(path))
        if kwargs.get("level") is not None:
            kwargs["level"] = cls.parse_level(kwargs["level"])
        return OutputConfig(**kwargs)

    @staticmethod
    def _format_from_path(path: str) -> LogFormat:
        suffix = Path(path).suffix
        if suffix:
            try:
                return LogFormat.from_string(suffix)
            except ValueError:
                pass
        return LogFormat.TEXT

    @staticmethod
    def _parse_keys(value: Any) -> list[str]:
        if isinstance(value, str):
            value = value.split(",")
        return [str(key).strip() for key in value if str(key).strip()]

    @staticmethod
    def _parse_bool(value: Any, name: str) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            text = value.strip().lower()
            if text in ("true", "1", "yes", "on"):
                return True
            if text in ("false", "0", "no", "off"):
                return False
        raise ValueError(f"Invalid boolean for {name!r}: {value!r}")

    @classmethod
    def _apply_env(cls, data: dict[str, Any], env: Mapping[str, str]) -> dict[str, Any]:
        result = dict(data)

        def get(name: str) -> str | None:
            value = env.get(cls.ENV_PREFIX + name)
            return value if value not in (None, "") else None

        if (value := get("LEVEL")) is not None:
            result["level"] = value
        if (value := get("MDC_KEYS")) is not None:
            result["mdc_keys"] = value
        if (value := get("STACK_TRACE")) is not None:
            result["include_stack_trace"] = value
        if (value := get("CAPTURE_UNCAUGHT")) is not None:
            result["capture_uncaught"] = value

        outputs = [dict(o) for o in result.get("outputs", [])]
        if (value := get("FILE")) is not None:
            outputs.append({"target": "file", "path": value})
        if (value := get("FORMAT")) is not None:
            outputs = outputs or [{}]
            for output in outputs:
                output["format"] = value
        if outputs:
            result["outputs"] = outputs
        return result
