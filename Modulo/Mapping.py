import os

from sortedcollections import SortedDict

from Modulo.Exceptions import *
from Modulo.Atomic import RWLock


class Mapping:
    STATUS_FREE = 0x00    # 可分配, 必须为 0x00
    STATUS_OCCUPY = 0x01  # 已分配
    STATUS_DYING = 0xFF   # 待擦除
    STATUS_BREAK = 0xC0   # 已损坏
    STATUS_SYS = 0xC1     # 系统用途

    def __init__(self, ssd, fp: str = "Mapping"):
        """
        创建虚拟 mapping 并打开
        :param ssd: 打开 ssd 的路径
        :param fp: 创建 mapping 的路径, 如果 mapping 已存在则直接打开
        """
        self.fp = fp
        self.ssd = ssd
        self.address_tot = ssd.size // ssd.pagesize  # ssd 保证可以整除
        self.address_len = self.__count_bits(self.address_tot) + 7 >> 3

        self.free_address_block = dict()  # {address: block_size}
        self.__free_address_block_r = dict()  # {after_tail_address: block_size}
        self.__free_blocks_dict = SortedDict()  # {block_size: [address...]} 支持二分查找

        self.occupy_address_block = dict()  # {address: block_size}

        self.__rwlock = RWLock()

        os.chdir(ssd.fp)
        if not os.path.exists(self.fp):
            self._init_mapping()

        self.__load_mapping()

    def address(self, pageno: int) -> tuple[int, int]:
        """
        返回地址在 flash 的真实地址
        :param pageno: 地址
        :return: (flash 编号, flash 地址)
        """
        with self.__rwlock.rlock():
            if self.mapping[pageno] != self.STATUS_OCCUPY:
                raise AccessError("Address {} is inaccessible".format(pageno))
            return pageno % self.ssd.flashes, pageno // self.ssd.flashes  # real address 可以直接计算得出

    def alloc(self, pages: int) -> int:
        """
        申请 ssd 空间, 计算合适的空间分配位置
        :param pages: 页数
        :return: 地址
        """
        if pages <= 0:
            raise AllocError("Number of pages should be positive")

        try:
            with self.__rwlock.wlock():
                # 获取申请 address
                _block_size, __ = self.__free_blocks_dict.peekitem(self.__free_blocks_dict.bisect_left(pages))
                _address = __.pop()
                if not __:
                    self.__free_blocks_dict.pop(_block_size)

                # 更新 mapping
                for i in range(pages):
                    self.mapping[_address + i] = self.STATUS_OCCUPY

                # 维护 free blocks
                _new_block_size = _block_size - pages
                self.free_address_block.pop(_address)
                if _new_block_size:
                    self.free_address_block[_address + pages] = _new_block_size
                    self.__free_address_block_r[_address + _block_size] = _new_block_size
                    if _new_block_size not in self.__free_blocks_dict:
                        self.__free_blocks_dict[_new_block_size] = []
                    self.__free_blocks_dict[_new_block_size].append(_address + pages)
                else:
                    self.__free_address_block_r.pop(_address + _block_size)

                # 维护 occupy blocks
                self.occupy_address_block[_address] = _block_size

                return _address

        except IndexError:
            raise AllocError("No enough space to alloc")

    def free(self, pageno: int) -> None:
        """
        释放 ssd 空间, 释放空间的大小自动计算
        :param pageno: 空间地址
        """
        # 获取释放空间大小, 同时维护 occupy blocks
        if pageno not in self.occupy_address_block:
            raise AccessError("Address {} is inaccessible".format(pageno))

        with self.__rwlock.wlock():
            _pages = self.occupy_address_block.pop(pageno)

            # 更新 mapping
            for i in range(_pages):
                self.mapping[pageno + i] = self.STATUS_FREE

            # 维护 free blocks
            _st, _ed = pageno, pageno + _pages
            # # 搜索前向拓展并移除
            if _st in self.__free_address_block_r:
                _block_size = self.__free_address_block_r.pop(_st)
                __ = self.__free_blocks_dict[_block_size]
                __.pop()
                if not __:
                    self.__free_blocks_dict.pop(_block_size)
                _st -= _block_size
            # # 搜索后向拓展并移除
            if _ed in self.free_address_block:
                _block_size = self.free_address_block.pop(_ed)
                __ = self.__free_blocks_dict[_block_size]
                __.pop()
                if not __:
                    self.__free_blocks_dict.pop(_block_size)
                _ed += _block_size
            # # 合并前向和后向拓展
            _block_size = _ed - _st
            self.__free_blocks_dict[_st] = _block_size
            self.__free_address_block_r[_ed] = _block_size
            if _block_size not in self.__free_blocks_dict:
                self.__free_blocks_dict[_block_size] = []
            self.__free_blocks_dict[_block_size].append(_st)

    def close(self):
        """关闭 mapping"""
        with self.__rwlock.wlock():
            self.__dump_mapping()

    def _init_mapping(self):
        """
        初始化映射文件, 映射文件格式为 (Bytes):
        0 ~ address_tot: 地址状态表, 状态由 STATUS_XXX 定义
        following every (1 + address_len * 2) Bytes:
            0 ~ 1: 状态 STATUS_XXX, 之后描述一个区间都是这个状态的
            # 重新计算区间的代价是巨大的, 维护区间的代价是较小的; 通过区间信息可以更高效管理 ssd 资源, 因此存储并维护这些信息是必要的
            1 ~ address_len + 1: 起始页索引
            address_len + 1 ~ : 区间页数
        """
        with open(self.fp, "wb") as _file:
            _file.write(self.__bytes_resize(
                self.STATUS_SYS.to_bytes(1, "little") * self.ssd.flashes,  # 系统用途, 具体为空指针
                self.address_tot
            ))
            _file.write(
                self.STATUS_FREE.to_bytes(1, "little") +
                self.__int2bytes(self.ssd.flashes) +
                self.__int2bytes(self.address_tot - self.ssd.flashes)
            )  # {address = ssd.flashes, block_size = address_tot}

    def __load_mapping(self):
        """读取 mapping"""
        with open(self.fp, "rb") as _file:
            self.mapping = bytearray(_file.read(self.address_tot))
            while True:
                __ = _file.read(self.address_len * 2)  # {address, block_size}
                if not __:
                    break
                _code = self.__bytes2int(__[:1])
                _address = self.__bytes2int(__[1: self.address_len + 1])
                _block_size = self.__bytes2int(__[self.address_len + 1:])
                if _code == self.STATUS_FREE:
                    self.free_address_block[_address] = _block_size
                    self.__free_address_block_r[_address + _block_size] = _block_size
                    if _block_size not in self.__free_blocks_dict:
                        self.__free_blocks_dict[_block_size] = []
                    self.__free_blocks_dict[_block_size].append(_address)
                elif _code == self.STATUS_OCCUPY:
                    self.occupy_address_block[_address] = _block_size

    def __dump_mapping(self):
        """保存 mapping"""
        with open(self.fp, "wb") as _file:
            _file.write(self.mapping)
            for _address, _block_size in self.free_address_block.items():
                _file.write(
                    self.STATUS_FREE.to_bytes(1, "little") +
                    self.__int2bytes(_address) +
                    self.__int2bytes(_block_size)
                )  # {address, block_size}
            for _address, _block_size in self.occupy_address_block.items():
                _file.write(
                    self.STATUS_OCCUPY.to_bytes(1, "little") +
                    self.__int2bytes(_address) +
                    self.__int2bytes(_block_size)
                )  # {address, block_size}

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

    @staticmethod
    def __bytes2int(b: bytes) -> int:
        """字节流转整型"""
        _i = 0
        for _b in reversed(b):
            _i <<= 8
            _i |= _b
        return _i

    def __int2bytes(self, i: int) -> bytes:
        """整型转字节流"""
        return i.to_bytes(self.address_len, "little")
