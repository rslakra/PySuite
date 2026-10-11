"""Document format converters.

Only the abstract base class is exported here. The registry (``get_converter``, ``list_conversions``,
``normalize_extension``, ...) lives in :mod:`pycrux.converter.registry`; importing it from this
``__init__`` would create a cycle, because the registry imports ``pycrux.office.word.converter``, which in
turn needs :class:`AbstractConverter` from this package.
"""

from pycrux.converter.abstract import AbstractConverter

__all__ = ["AbstractConverter"]
