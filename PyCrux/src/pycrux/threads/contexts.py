"""Thread-local stack of attribute contexts with scoped attribute inheritance."""

__author__ = "Rohtash Lakra"
__copyright__ = "Copyright 2025, Rohtash Lakra"
__credits__ = ["Rohtash Lakra"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Rohtash Lakra"
__email__ = "rslakra@ameyllc.com"
__status__ = "Production"

import threading

__all__ = ["Context", "ContextStack", "StackUnderflow"]


class StackUnderflow(Exception):
    """Raised when popping the last remaining context from a ``ContextStack``."""


class Context(object):
    """Attribute namespace that falls back to its parent context on lookup."""

    __slots__ = ["_parent", "_dict"]

    def __init__(self, parent=None):
        """Initialize Context"""
        assert parent is None or isinstance(parent, Context)
        super(Context, self).__init__()
        object.__setattr__(self, "_parent", parent)
        object.__setattr__(self, "_dict", {})

    @property
    def _parents(self):
        entry = self
        while entry:
            yield entry
            entry = entry._parent

    def __getattr__(self, attr):
        for entry in self._parents:
            if attr in entry._dict:
                return entry._dict[attr]

        raise AttributeError(attr)

    def __delattr__(self, attr):
        del self._dict[attr]

    def __setattr__(self, attr, value):
        self._dict[attr] = value

    def __dir__(self):
        dir_set = set()
        for entry in self._parents:
            dir_set.update(entry._dict)

        return list(dir_set)


class _ThreadStack(threading.local):
    """Per-thread storage for a ``ContextStack``.

    ``threading.local`` calls ``__init__`` again, with the same arguments, the first time each thread
    touches the object, so every thread gets its own stack whose bottom frame inherits from ``base``.
    """

    def __init__(self, base: Context) -> None:
        super().__init__()
        self.stack = [Context(base)]


class ContextStack(object):
    """Thread-local stack of ``Context`` objects.

    Attribute access is delegated to the top-most context. Use ``push()`` /
    ``pop()`` or the ``with`` statement to scope changes.
    """

    __slots__ = ["_local", "base"]

    # Convenience alias so callers can write ``ContextStack.StackUnderflow``.
    StackUnderflow = StackUnderflow

    def __init__(self):
        """Initialize ContextStack"""
        super(ContextStack, self).__init__()
        object.__setattr__(self, "base", Context())
        object.__setattr__(self, "_local", _ThreadStack(self.base))

    @property
    def _heap(self):
        if self._local.stack:
            return self._local.stack[-1]

        else:
            return self.base

    def __iter__(self):
        yield self.base
        for itr in self._local.stack:
            yield itr

    def __getattr__(self, attr):
        return getattr(self._heap, attr)

    def __setattr__(self, attr, value):
        return setattr(self._heap, attr, value)

    def __delattr__(self, attr):
        return delattr(self._heap, attr)

    def push(self):
        new_context = Context(self._heap)
        self._local.stack.append(new_context)
        return new_context

    def pop(self):
        if len(self._local.stack) == 1:
            raise StackUnderflow()

        self._local.stack.pop(-1)

    def __enter__(self):
        return self.push()

    def __exit__(self, *exc):
        self.pop()

    def __dir__(self):
        dir_set = set()
        for entry in self:
            dir_set.update(entry._dict)

        return list(dir_set)

    def __getitem__(self, index):
        assert index <= 0
        return self._local.stack[index - 1]

    def __len__(self):
        return len(self._local.stack)
