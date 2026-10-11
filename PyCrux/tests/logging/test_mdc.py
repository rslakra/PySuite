"""Tests for ``pycrux.logging.mdc`` — ``MDC``, ``MDCScope`` and ``RequestScope``."""

import contextvars
import re
import threading

import pytest

from pycrux.logging import MDC, MDCScope, RequestScope

# --- MDC facade ---------------------------------------------------------------


def test_request_id_key() -> None:
    assert MDC.REQUEST_ID_KEY == "requestId"


def test_put_get_remove_clear() -> None:
    MDC.put("a", 1)
    MDC.put("b", 2)
    assert MDC.get("a") == 1
    assert MDC.get("zzz") is None
    assert MDC.get("zzz", "dflt") == "dflt"

    MDC.remove("a")
    MDC.remove("a")  # absent key is not an error
    assert MDC.get_all() == {"b": 2}

    MDC.clear()
    assert MDC.get_all() == {}


def test_put_converts_key_to_str() -> None:
    MDC.put(5, "five")  # type: ignore[arg-type]
    assert MDC.get("5") == "five"


def test_get_all_returns_a_copy() -> None:
    MDC.put("a", 1)
    MDC.get_all()["a"] = 99
    assert MDC.get("a") == 1


def test_set_all_replaces_everything() -> None:
    MDC.put("old", 1)
    MDC.set_all({"new": 2, 3: "three"})  # type: ignore[dict-item]
    assert MDC.get_all() == {"new": 2, "3": "three"}


def test_mutating_after_put_does_not_leak_into_previous_snapshots() -> None:
    MDC.put("a", 1)
    snapshot = MDC.get_all()
    MDC.put("b", 2)
    assert snapshot == {"a": 1}


# --- MDC.scope / MDCScope ------------------------------------------------------


def test_scope_adds_and_restores() -> None:
    MDC.put("keep", 1)
    with MDC.scope({"a": 1}, b=2) as scope:
        assert isinstance(scope, MDCScope)
        assert MDC.get_all() == {"keep": 1, "a": 1, "b": 2}
    assert MDC.get_all() == {"keep": 1}


def test_scope_overrides_then_restores_existing_key() -> None:
    MDC.put("a", "outer")
    with MDC.scope(a="inner"):
        assert MDC.get("a") == "inner"
    assert MDC.get("a") == "outer"


def test_scope_restores_on_exception() -> None:
    with pytest.raises(RuntimeError):
        with MDC.scope(a=1):
            raise RuntimeError("boom")
    assert MDC.get_all() == {}


def test_scope_without_values_is_a_noop() -> None:
    MDC.put("a", 1)
    with MDC.scope():
        assert MDC.get_all() == {"a": 1}
    assert MDC.get_all() == {"a": 1}


def test_scope_object_is_reentrant() -> None:
    scope = MDCScope(a=1)
    with scope:
        MDC.put("inner", True)
        with scope:
            assert MDC.get("a") == 1
        assert MDC.get("inner") is True
    assert MDC.get_all() == {}


def test_scope_converts_keys_to_str() -> None:
    with MDC.scope({7: "x"}):  # type: ignore[dict-item]
        assert MDC.get("7") == "x"


# --- MDC.request_scope / RequestScope --------------------------------------------


def test_request_scope_generates_an_id() -> None:
    with MDC.request_scope(userId="42") as request_id:
        assert re.fullmatch(r"[0-9a-f]{32}", request_id)
        assert MDC.get("requestId") == request_id
        assert MDC.get("userId") == "42"
    assert MDC.get_all() == {}


def test_request_scope_uses_given_id_and_is_a_request_scope() -> None:
    scope = MDC.request_scope("req-1", tenant="t")
    assert isinstance(scope, RequestScope)
    assert scope.request_id == "req-1"
    with scope as request_id:
        assert request_id == "req-1"
        assert MDC.get_all() == {"requestId": "req-1", "tenant": "t"}


def test_request_scope_ids_are_unique() -> None:
    assert RequestScope().request_id != RequestScope().request_id


# --- isolation ------------------------------------------------------------------


def test_new_thread_starts_with_empty_mdc() -> None:
    MDC.put("main", 1)
    seen: list[dict] = []
    thread = threading.Thread(target=lambda: seen.append(MDC.get_all()))
    thread.start()
    thread.join()
    assert seen == [{}]


def test_copied_context_carries_mdc_into_a_thread() -> None:
    MDC.put("main", 1)
    ctx = contextvars.copy_context()
    seen: list[dict] = []
    thread = threading.Thread(target=lambda: seen.append(ctx.run(MDC.get_all)))
    thread.start()
    thread.join()
    assert seen == [{"main": 1}]
