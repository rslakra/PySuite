import pytest

from pycrux.threads import ContextStack, StackUnderflow


def test_simple_push_pop() -> None:
    c = ContextStack()

    c.a = 42
    assert c.a == 42

    c.push()
    assert c.a == 42
    c.a = 24
    assert c.a == 24
    c.pop()

    assert c.a == 42


def test_simple_context() -> None:
    c = ContextStack()

    c.a = 42
    assert c.a == 42

    with c:
        assert c.a == 42

        c.a = 24
        assert c.a == 24

    assert c.a == 42


def test_del() -> None:
    c = ContextStack()

    c.a = 42
    assert c.a == 42

    del c.a

    with pytest.raises(AttributeError):
        c.a


def test_del_push() -> None:
    c = ContextStack()

    c.a = 42
    assert c.a == 42

    with c:
        assert c.a == 42

        c.a = 24
        assert c.a == 24

        del c.a
        assert c.a == 42

    assert c.a == 42


def test_underflow() -> None:
    c = ContextStack()

    with pytest.raises(ContextStack.StackUnderflow):
        c.pop()

    with pytest.raises(StackUnderflow):
        c.pop()


def test_dir() -> None:
    c = ContextStack()

    c.a = 42

    assert "a" in dir(c)

    with c:
        assert "a" in dir(c)

    assert "a" in dir(c)

    del c.a
    assert "a" not in dir(c)


def test_len() -> None:
    c = ContextStack()

    assert len(c) == 1
    with c:
        assert len(c) == 2
        with c:
            assert len(c) == 3
        assert len(c) == 2
    assert len(c) == 1


def test_inherit() -> None:
    c = ContextStack()

    c.a = 42
    assert c.a == 42

    with c:
        assert c.a == 42

        c[-1].a = "foo"
        assert c.a == "foo"

        c.a = 24
        assert c.a == 24
        assert c[-1].a == "foo"

        del c.a
        assert c.a == "foo"

    assert c.a == "foo"


def test_base() -> None:
    c = ContextStack()

    c.base.a = 42

    assert c.base.a == 42
    assert c.a == 42

    c.a = 24
    assert c.a == 24

    del c.a
    assert c.a == 42
