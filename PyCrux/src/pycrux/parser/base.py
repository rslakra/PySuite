class Parser(object):
    """Base class for all parsers."""

    def __init__(self):
        pass

    def parse(self, data):
        raise NotImplementedError
