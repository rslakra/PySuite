import threading


class Singleton:
    """Creates a singleton instance"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # check if the instance is already initialize or not
        if not cls._instance:
            # take lock
            with cls._lock:
                # double check if the instance is initialized or not
                if not cls._instance:
                    cls._instance = super(Singleton, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        self.counter = 0


instance = Singleton()
if __name__ == '__main__':
    print(instance)
    print(instance.__class__)
    print(instance.counter)
    print(instance)
    print(instance.__class__)
    print(instance.counter)

