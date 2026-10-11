"""Logger setup: handlers, MDC injection and uncaught-exception capture.

Typical use::

    from pycrux.logging import MDC, LogManager

    LogManager.configure({"outputs": [{"format": "json", "target": "file", "path": "logs/app"}]})
    log = LogManager.get_logger(__name__)

    with MDC.request_scope(userId="42"):
        try:
            handle()
        except Exception:
            log.exception("Request failed")   # full stack + cause chain + MDC
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import threading
from collections.abc import Mapping
from typing import Any, ClassVar

from .config import LogConfig, OutputConfig
from .formatters import FormatterFactory
from .mdc import MDC
from .parser import LogConfigParser
from .types import LogTarget


class MDCFilter(logging.Filter):
    """Attach the current MDC snapshot to each record as ``record.mdc``.

    Handlers run this filter in the thread that emitted the record, so the
    snapshot reflects the caller's context even for later (e.g. queued) output.

    Args:
        keys: MDC keys to keep, in order (``None`` / empty = keep all).
        defaults: Entries added to every record; MDC values override them.
    """

    def __init__(self, keys: tuple[str, ...] | None = None, defaults: Mapping[str, Any] | None = None) -> None:
        super().__init__()
        self._keys = tuple(keys) if keys else None
        self._defaults = dict(defaults or {})

    def filter(self, record: logging.LogRecord) -> bool:
        context = {**self._defaults, **MDC.get_all()}
        if self._keys is not None:
            context = {key: context[key] for key in self._keys if key in context}
        record.mdc = context
        return True


class HandlerFactory:
    """Creates the stdlib handler for an :class:`OutputConfig`."""

    @staticmethod
    def create(output: OutputConfig, config: LogConfig) -> logging.Handler:
        """Create a handler with its formatter and MDC filter attached."""
        handler: logging.Handler
        if output.target is LogTarget.FILE:
            path = output.resolved_path()
            assert path is not None
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.handlers.RotatingFileHandler(
                path,
                maxBytes=output.max_bytes,
                backupCount=output.backup_count,
                encoding=output.encoding,
                delay=True,
            )
        else:
            handler = logging.StreamHandler(sys.stdout if output.stream == "stdout" else sys.stderr)

        if output.level is not None:
            handler.setLevel(output.level)
        handler.setFormatter(
            FormatterFactory.create(
                output.format,
                pattern=output.pattern,
                include_stack_trace=config.include_stack_trace,
            )
        )
        handler.addFilter(MDCFilter(config.mdc_keys, config.mdc_defaults))
        return handler


class UncaughtExceptionHandler:
    """Logs uncaught exceptions (main and worker threads) at ``CRITICAL`` with the full stack.

    :meth:`install` replaces ``sys.excepthook`` and ``threading.excepthook``;
    :meth:`uninstall` restores the previous hooks (only if they are still ours).
    """

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._previous_sys: Any = None
        self._previous_thread: Any = None
        self._sys_hook: Any = None
        self._thread_hook: Any = None

    @property
    def installed(self) -> bool:
        return self._sys_hook is not None

    def install(self) -> None:
        if self.installed:
            return
        self._previous_sys = sys.excepthook
        self._previous_thread = threading.excepthook
        self._sys_hook = self._on_uncaught
        self._thread_hook = self._on_thread_uncaught
        sys.excepthook = self._sys_hook
        threading.excepthook = self._thread_hook

    def uninstall(self) -> None:
        if not self.installed:
            return
        if sys.excepthook is self._sys_hook:
            sys.excepthook = self._previous_sys
        if threading.excepthook is self._thread_hook:
            threading.excepthook = self._previous_thread
        self._sys_hook = self._thread_hook = None

    def _on_uncaught(self, exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            self._previous_sys(exc_type, exc_value, exc_traceback)
            return
        self._logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    def _on_thread_uncaught(self, args: threading.ExceptHookArgs) -> None:
        if args.exc_type is SystemExit:
            return
        thread_name = args.thread.name if args.thread else "unknown"
        self._logger.critical(
            "Uncaught exception in thread %s",
            thread_name,
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )


class LogManager:
    """Entry point: configure logging once at startup, then fetch loggers anywhere.

    State is kept on the class, so :meth:`configure` / :meth:`shutdown` act on
    one process-wide setup. Calling :meth:`configure` again replaces it.
    """

    _lock: ClassVar[threading.RLock] = threading.RLock()
    _logger_name: ClassVar[str] = ""
    _handlers: ClassVar[list[logging.Handler]] = []
    _previous_levels: ClassVar[dict[str, int]] = {}
    _uncaught: ClassVar[UncaughtExceptionHandler | None] = None

    @classmethod
    def get_logger(cls, name: str | None = None) -> logging.Logger:
        """Return the logger for ``name`` (the root logger when ``None``)."""
        return logging.getLogger(name)

    @classmethod
    def configure(
        cls,
        config: LogConfig | Mapping[str, Any] | str | os.PathLike[str] | None = None,
        *,
        name: str = "",
        env: Mapping[str, str] | None = None,
    ) -> logging.Logger:
        """Configure logging and return the configured logger.

        Args:
            config: A ``LogConfig``, a config mapping, the path of a ``.json``
                config file, or ``None`` for the defaults (INFO, text, stderr).
            name: Logger to attach the handlers to. The default (root) covers
                every logger in the application; pass a package name to scope it.
            env: Pass ``os.environ`` to apply ``PYCRUX_LOG_*`` overrides.
        """
        cfg = LogConfigParser.parse(config, env=env)
        with cls._lock:
            cls.shutdown()
            logger = logging.getLogger(name)
            cls._logger_name = name

            cls._remember_level(logger)
            logger.setLevel(cfg.level)
            for logger_name, level in cfg.levels.items():
                other = logging.getLogger(logger_name)
                cls._remember_level(other)
                other.setLevel(level)

            handlers = [HandlerFactory.create(output, cfg) for output in cfg.outputs]
            for handler in handlers:
                logger.addHandler(handler)
            cls._handlers = handlers

            if cfg.capture_uncaught:
                cls._uncaught = UncaughtExceptionHandler(logger)
                cls._uncaught.install()
        return logger

    @classmethod
    def shutdown(cls) -> None:
        """Remove and close the installed handlers; restore levels and exception hooks."""
        with cls._lock:
            logger = logging.getLogger(cls._logger_name)
            for handler in cls._handlers:
                logger.removeHandler(handler)
                handler.close()
            for logger_name, level in cls._previous_levels.items():
                logging.getLogger(logger_name).setLevel(level)
            if cls._uncaught is not None:
                cls._uncaught.uninstall()
            cls._handlers = []
            cls._previous_levels = {}
            cls._uncaught = None

    @classmethod
    def _remember_level(cls, logger: logging.Logger) -> None:
        name = "" if logger.name == "root" else logger.name
        cls._previous_levels.setdefault(name, logger.level)
