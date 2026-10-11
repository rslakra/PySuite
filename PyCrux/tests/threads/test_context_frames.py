"""Tests for ``pycrux.threads.contexts.Context`` and the thread-local behaviour of ``ContextStack``."""

import threading

import pytest

from pycrux.threads import Context, ContextStack, StackUnderflow
from pycrux.threads.contexts import _ThreadStack

# --- Context -----------------------------------------------------------------------


def test_context_set_get_and_missing_attribute() -> None:
    ctx = Context()
    ctx.name = "x"
    assert ctx.name == "x"
    with pytest.raises(AttributeError):
        ctx.missing


def test_context_lookup_falls_back_to_parent() -> None:
    parent = Context()
    parent.a = 1
    parent.b = 2
    child = Context(parent)
    child.b = 20

    assert child.a == 1
    assert child.b == 20
    assert parent.b == 2


def test_context_delete_only_affects_own_frame() -> None:
    parent = Context()
    parent.a = 1
    child = Context(parent)
    child.a = 2

    del child.a
    assert child.a == 1

    with pytest.raises(KeyError):
        del child.a


def test_context_dir_includes_parent_attributes() -> None:
    parent = Context()
    parent.a = 1
    child = Context(parent)
    child.b = 2

    assert sorted(a for a in dir(child) if a in {"a", "b"}) == ["a", "b"]
    assert "b" not in dir(parent)


def test_context_parent_must_be_a_context() -> None:
    with pytest.raises(AssertionError):
        Context(parent=object())  # type: ignore[arg-type]


# --- ContextStack API details ------------------------------------------------------


def test_stack_underflow_is_exposed_on_the_class() -> None:
    assert ContextStack.StackUnderflow is StackUnderflow
    assert issubclass(StackUnderflow, Exception)


def test_push_returns_the_new_top_context() -> None:
    c = ContextStack()
    top = c.push()
    assert isinstance(top, Context)
    top.value = 5
    assert c.value == 5
    c.pop()
    with pytest.raises(AttributeError):
        c.value


def test_with_block_yields_context_and_pops_on_error() -> None:
    c = ContextStack()
    c.a = 1
    with pytest.raises(RuntimeError):
        with c as frame:
            assert isinstance(frame, Context)
            c.a = 2
            raise RuntimeError("boom")
    assert c.a == 1
    assert len(c) == 1


def test_iteration_yields_base_then_frames() -> None:
    c = ContextStack()
    c.push()
    frames = list(c)
    assert frames[0] is c.base
    assert len(frames) == len(c) + 1


def test_getitem_requires_non_positive_index() -> None:
    c = ContextStack()
    with c:
        assert c[0] is c._local.stack[-1]
        assert c[-1] is c._local.stack[-2]
    with pytest.raises(AssertionError):
        c[1]


def test_base_is_shared_by_every_level() -> None:
    c = ContextStack()
    c.base.shared = "yes"
    with c:
        with c:
            assert c.shared == "yes"


def test_heap_falls_back_to_base_when_stack_is_empty() -> None:
    c = ContextStack()
    c.base.only_base = 1
    c._local.stack.clear()
    assert c._heap is c.base
    assert c.only_base == 1


# --- thread isolation ------------------------------------------------------------


def _run_in_thread(target) -> None:
    errors: list[BaseException] = []

    def runner() -> None:
        try:
            target()
        except BaseException as exc:  # noqa: BLE001 - re-raised in the main thread
            errors.append(exc)

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()
    if errors:
        raise errors[0]


def test_each_thread_gets_its_own_stack() -> None:
    c = ContextStack()
    c.shared = "main"
    c.base.root_value = "root"
    seen: dict[str, object] = {}

    def worker() -> None:
        # a new thread starts with one frame on top of ``base`` and does not see main-thread frames
        seen["len"] = len(c)
        seen["root_value"] = c.root_value
        with pytest.raises(AttributeError):
            c.shared
        c.shared = "worker"
        c.push()
        seen["pushed_len"] = len(c)

    _run_in_thread(worker)

    assert seen == {"len": 1, "root_value": "root", "pushed_len": 2}
    assert c.shared == "main"
    assert len(c) == 1


def test_pop_in_a_new_thread_underflows_independently() -> None:
    c = ContextStack()
    c.push()
    c.push()

    def worker() -> None:
        with pytest.raises(StackUnderflow):
            c.pop()

    _run_in_thread(worker)
    assert len(c) == 3


def test_thread_stack_initialises_once_per_thread() -> None:
    base = Context()
    local = _ThreadStack(base)
    first = local.stack
    assert local.stack is first
    assert len(first) == 1

    other: list[object] = []
    _run_in_thread(lambda: other.append(local.stack))
    assert other[0] is not first
