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


class RWLock:
    class __RLock:
        def __init__(self, rwlock: Lock):
            self.__global = rwlock
            self.__mutex = Lock()
            self.__i = 0

        def acquire(self):
            with self.__mutex:
                if not self.__i:
                    self.__global.acquire()
                self.__i += 1

        def release(self):
            with self.__mutex:
                if not self.__i:
                    raise CounterError("Unexpected Negative Count")
                self.__i -= 1
                if not self.__i:
                    self.__global.release()

        def __enter__(self):
            return self.acquire()

        def __exit__(self, *args):
            self.release()

    class __WLock:
        def __init__(self, rwlock: Lock):
            self.__global = rwlock

        def acquire(self):
            self.__global.acquire()

        def release(self):
            self.__global.release()

        def __enter__(self):
            return self.acquire()

        def __exit__(self, *args):
            self.release()

    def __init__(self):
        self.__global = Lock()
        self.__rlock = self.__RLock(self.__global)
        self.__wlock = self.__WLock(self.__global)

    def rlock(self):
        return self.__rlock

    def wlock(self):
        return self.__wlock
