from threading import Lock


class CounterError(Exception):
    """计数器错误"""
    def __init__(self, msg=""):
        super().__init__(msg)


class Waiter:
    def __init__(self, num: int = 0):
        self.i = num
        self.mutex = Lock()

    def inc(self):
        with self.mutex:
            self.i += 1

    def dec(self):
        with self.mutex:
            if self.i == 0:
                raise CounterError("Unexpected Negative Count")
            self.i -= 1

    def __bool__(self) -> bool:
        return bool(self.i)
