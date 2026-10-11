class Formatter(object):
    """Base class for all formatters."""

    def __init__(self):
        pass

    def format(self, value):
        raise NotImplementedError
    