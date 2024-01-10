import os
from queue import Queue
from threading import Thread

import yaml

from Modulo.Exceptions import *
from Modulo.Flash import Flash
from Modulo.Mapping import Mapping
from Modulo.Atomic import Waiter


class SSD:
    def __init__(self, fp: str, size: int, flashes: int = 8, pagesize: int = 4 << 10):
        """
        创建虚拟 ssd 并打开, 同时指定 ssd 的大小, flash 的数量, page 的大小
        :param fp: 创建 ssd 的路径, 如果 ssd 已创建, 将直接打开并忽略其他参数
        :param size: 指定 ssd 的大小 (Bytes), 如果大小不合适, 将自动调整合适值
        :param flashes: 指定 flash 的数量
        :param pagesize: 指定 page 的大小 (Bytes), 如果大小不合适, 将自动调整合适值
        """
        if os.path.exists(fp) and os.path.exists("SSD.yml"):
            # ssd 已存在
            self.fp = fp
            os.chdir(self.fp)

            self.__read_config()
        else:
            # ssd 未创建
            self.fp = fp
            if not os.path.exists(self.fp):
                os.mkdir(self.fp)
            os.chdir(self.fp)
            self.__page_bits = self.__count_bits(pagesize)
            self.pagesize = 1 << self.__page_bits
            self.flashes = max(flashes, 1)
            __ = self.flashes * self.pagesize
            self.size = (max(size, 1) + __ - 1) // __ * __
            self.flash = ["Flash{:02d}".format(__) for __ in range(self.flashes)]

            self.__write_config()
        self.__open_flash()
        self.__open__mapping()

    def list(self) -> list:
        """
        返回当前占用地址, 返回格式如下:
        返回 list, 其元素为 tuple(起始地址, 占用长度)
        """
        return sorted([
            (_pageno << self.__page_bits, _pages << self.__page_bits)
            for _pageno, _pages in self._mapping.occupy_address_block.items()
        ])

    def create(self, size: int) -> int:
        """申请虚拟 ssd 为 size 的内存, 返回创建地址"""
        return self._mapping.alloc(size + self.pagesize - 1 >> self.__page_bits) << self.__page_bits

    def copy_in(self, fp: str, address: int) -> None:
        """从本地拷贝到虚拟 ssd, 覆盖目标地址, 大小不足将抛出异常"""
        _pageno = address >> self.__page_bits
        _pages = os.stat(fp).st_size + self.pagesize - 1 >> self.__page_bits
        if _pageno not in self._mapping.occupy_address_block:
            raise AccessError("Address {} is inaccessible".format(_pageno))
        if _pages > self._mapping.occupy_address_block.get[_pageno]:
            raise CopySizeError("Copy space is not enough")
        with Waiter(_pages) as _waiter:
            for i in range(0, _pages):
                _flashno, _flashpageno = self._mapping.address(_pageno + i)
                self.__from_queue[_flashno].put((
                    Flash.INSTRUCT_WRITE_FROM_FILE,
                    _waiter,
                    fp,
                    i << self.__page_bits,
                    _flashpageno,
                ))

    def copy_out(self, address: int, fp: str, size: int) -> None:
        """从虚拟 ssd 拷贝到本地, 必须指定本地路径和本地文件大小"""
        _pageno = address >> self.__page_bits
        _pages = size + self.pagesize - 1 >> self.__page_bits
        if _pageno not in self._mapping.occupy_address_block:
            raise AccessError("Address {} is inaccessible".format(_pageno))
        if _pages > self._mapping.occupy_address_block.get[_pageno]:
            raise CopySizeError("Copy space is not enough")
        with open(fp, "wb"):
            pass
        with Waiter(_pages) as _waiter:
            for i in range(0, _pages):
                _flashno, _flashpageno = self._mapping.address(_pageno + i)
                self.__from_queue[_flashno].put((
                    Flash.INSTRUCT_READ_INTO_FILE,
                    _waiter,
                    _flashpageno,
                    fp,
                    i << self.__page_bits,
                ))

    def delete(self, address: int) -> None:
        """释放虚拟 ssd 目标地址"""
        self._mapping.free(address >> self.__page_bits)

    def close(self):
        """关闭 ssd"""
        self._mapping.close()
        with Waiter(self.flashes) as _waiter:
            for i in range(self.flashes):
                self.__from_queue[i].put((Flash.INSTRUCT_EXIT, _waiter))

    def __read_config(self) -> None:
        """读取配置"""
        with open("SSD.yml", "r", encoding="utf-8") as _file:
            _data = yaml.safe_load(_file)
            self.size = _data["size"]
            self.pagesize = _data["pagesize"]
            self.flashes = len(_data["flash"])
            self.flash = _data["flash"]

    def __write_config(self) -> None:
        """写入配置"""
        with open("SSD.yml", "w", encoding="utf-8") as _file:
            yaml.safe_dump({
                "size": self.size,
                "pagesize": self.pagesize,
                "flash": [__ for __ in self.flash],
            }, _file)

    def __open_flash(self) -> None:
        self.__flash = []
        self.__from_queue = []
        for i in range(self.flashes):
            self.__from_queue.append(Queue())
        for i in range(self.flashes):
            self.__flash.append(Thread(
                target=Flash,
                name=self.flash[i],
                args=(self, self.__from_queue[i], self.flash[i])
            ))
            self.__flash[-1].start()

    def __open__mapping(self) -> None:
        self._mapping = Mapping(self)

    @staticmethod
    def __count_bits(x: int) -> int:
        """返回整型位数"""
        if x <= 2:
            return 1
        x -= 1
        _cnt = 0
        while x:
            x >>= 1
            _cnt += 1
        return _cnt

    @staticmethod
    def __bytes_resize(b: bytes, length: int) -> bytes:
        """将字节流调整到定长, 长截断, 短补零"""
        if len(b) == length:
            return b
        if len(b) > length:
            return b[:length]
        return b + b"\x00" * (length - len(b))
