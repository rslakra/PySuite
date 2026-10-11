class ThreadSessions(object):
    """Thread-local session storage."""

    def __init__(self):
        self._local = threading.local()

    def __getattr__(self, attr):
        return getattr(self._local, attr)

    def __setattr__(self, attr, value):
        setattr(self._local, attr, value)
