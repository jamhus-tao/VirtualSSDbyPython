from threading import Lock


class CounterError(Exception):
    """计数器错误"""
    def __init__(self, msg=""):
        super().__init__(msg)


class Waiter:
    def __init__(self, num: int = 0):
        if num < 0:
            raise CounterError("Unexpected Negative Count")
        self.__i = num
        self.__mutex = Lock()

    def inc(self):
        with self.__mutex:
            self.__i += 1

    def dec(self):
        with self.__mutex:
            if self.__i == 0:
                raise CounterError("Unexpected Negative Count")
            self.__i -= 1

    def wait(self):
        while self.__i:
            pass

    def __bool__(self) -> bool:
        return bool(self.__i)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.wait()
