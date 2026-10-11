"""Thread-local context stack with scoped attribute inheritance."""

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
    """Raised when pop() is called with only the root frame on the stack."""


class ContextStack:
    """Thread-local stack of Context frames with attribute inheritance."""

    __slots__ = ["_local", "base"]

    StackUnderflow = StackUnderflow

    def __init__(self):
        object.__setattr__(self, "base", Context())
        object.__setattr__(self, "_local", threading.local())
        self._local.stack = [Context(self.base)]

    @property
    def _heap(self):
        if self._local.stack:
            return self._local.stack[-1]
        return self.base

    def __iter__(self):
        yield self.base
        yield from self._local.stack

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

        self._local.stack.pop()

    def __enter__(self):
        return self.push()

    def __exit__(self, *_exc):
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


class Context:
    """A single context frame; resolves attributes through parent chain."""

    __slots__ = ["_parent", "_dict"]

    def __init__(self, parent=None):
        assert parent is None or isinstance(parent, Context)
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
