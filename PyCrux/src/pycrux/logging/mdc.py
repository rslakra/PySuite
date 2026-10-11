"""Mapped Diagnostic Context (MDC).

Binds diagnostic data (``requestId``, ``userId``, ``sessionId`` ...) to the
current execution context so every log statement can include it without
passing it through each call.

The context is stored in a :class:`contextvars.ContextVar`, which gives:

* **Thread isolation** — each thread has its own map (a new thread starts empty).
* **asyncio support** — each task works on a copy of its parent's map.

To carry the map into a worker thread, run the callable inside a copied context::

    ctx = contextvars.copy_context()
    executor.submit(ctx.run, work)
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from contextvars import ContextVar
from types import MappingProxyType, TracebackType
from typing import Any, ClassVar

_EMPTY: Mapping[str, Any] = MappingProxyType({})


class MDCScope:
    """Context manager that adds entries to the MDC for a ``with`` block.

    The previous map is restored on exit, also when the block raises. Instances
    are re-entrant (the same scope object may be nested).
    """

    def __init__(self, values: Mapping[str, Any] | None = None, **kwargs: Any) -> None:
        self._values: dict[str, Any] = {str(k): v for k, v in (values or {}).items()}
        self._values.update(kwargs)
        self._previous: list[Mapping[str, Any]] = []

    def __enter__(self) -> MDCScope:
        previous = MDC._context.get()
        self._previous.append(previous)
        MDC._context.set({**previous, **self._values})
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        MDC._context.set(self._previous.pop())


class RequestScope(MDCScope):
    """:class:`MDCScope` that also binds a ``requestId`` (generated when omitted).

    Every log line emitted inside the block carries the ``requestId``, which lets
    you follow the complete flow of one request. ``with ... as request_id`` yields
    the id.
    """

    def __init__(self, request_id: str | None = None, **values: Any) -> None:
        self.request_id = request_id or uuid.uuid4().hex
        super().__init__({MDC.REQUEST_ID_KEY: self.request_id}, **values)

    def __enter__(self) -> str:  # type: ignore[override]
        super().__enter__()
        return self.request_id


class MDC:
    """Facade over the current context map (same API as SLF4J's ``MDC``)."""

    REQUEST_ID_KEY: ClassVar[str] = "requestId"

    _context: ClassVar[ContextVar[Mapping[str, Any]]] = ContextVar("pycrux_logging_mdc", default=_EMPTY)

    @classmethod
    def put(cls, key: str, value: Any) -> None:
        """Insert a key/value pair into the current context map."""
        data = dict(cls._context.get())
        data[str(key)] = value
        cls._context.set(data)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Return the value for ``key``, or ``default`` if absent."""
        return cls._context.get().get(key, default)

    @classmethod
    def remove(cls, key: str) -> None:
        """Delete ``key`` from the context map (no error if it is absent)."""
        current = cls._context.get()
        if key in current:
            data = dict(current)
            del data[key]
            cls._context.set(data)

    @classmethod
    def clear(cls) -> None:
        """Remove every entry from the context map."""
        cls._context.set(_EMPTY)

    @classmethod
    def get_all(cls) -> dict[str, Any]:
        """Return a copy of the whole context map."""
        return dict(cls._context.get())

    @classmethod
    def set_all(cls, values: Mapping[str, Any]) -> None:
        """Replace the whole context map with ``values``."""
        cls._context.set({str(k): v for k, v in values.items()})

    @staticmethod
    def scope(values: Mapping[str, Any] | None = None, **kwargs: Any) -> MDCScope:
        """Add entries for a ``with`` block, then restore the previous map."""
        return MDCScope(values, **kwargs)

    @staticmethod
    def request_scope(request_id: str | None = None, **values: Any) -> RequestScope:
        """Bind a ``requestId`` (generated when omitted) plus extra entries for a block."""
        return RequestScope(request_id, **values)
