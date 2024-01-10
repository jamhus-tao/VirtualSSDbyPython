from sortedcollections import SortedDict


class SortedMultiDict:
    def __init__(self, *args, **kwargs):
        """支持二分查找的可重字典"""
        self.__ = SortedDict(*args, **kwargs)

    def pop_ge(self, item):
        """
        pop 一个大于等于 item 的最小元素, 存在同等小时 pop 最近加入的
        :param item: pop 的元素, 实际 pop 的是大于等于它的
        :return: (key, value); 不存在大于等于它时抛出 IndexError
        """
        _idx = self.__.bisect_left(item)
        _key, _ = self.__.peekitem(_idx)
        return _key, self.pop(_key)

    def pop(self, item):
        """
        pop 一个元素, 存在多个时 pop 最近加入的
        :param item: pop 的元素, 必须相等
        :return: (key, value); 不存在时抛出 KeyError
        """
        __ = self.__[item]
        _value = __.pop()
        if not __:
            self.__.pop(item)
        return _value

    def add(self, key, value):
        """
        添加一个元素
        :param key:
        :param value:
        :return:
        """
        if key not in self.__:
            self.__[key] = []
        self.__[key].append(value)

    def __repr__(self):
        return self.__.__repr__()
