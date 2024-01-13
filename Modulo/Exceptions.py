class OutOfBoundError(Exception):
    def __init__(self, message=""):
        """地址越界错误"""
        super().__init__(message)


class AccessError(Exception):
    def __init__(self, message=""):
        """无权访问错误"""
        super().__init__(message)


class AllocError(Exception):
    def __init__(self, message=""):
        """内存申请错误"""
        super().__init__(message)


class CopySizeError(Exception):
    def __init__(self, message=""):
        """拷贝空间错误"""
        super().__init__(message)
