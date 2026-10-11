class Temporal(object):
    """Base class for all temporal classes."""

    def __init__(self):
        pass

    def __eq__(self, other):
        raise NotImplementedError

    def __hash__(self):
        raise NotImplementedError
