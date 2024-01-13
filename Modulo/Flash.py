import os
from queue import Queue
from threading import Thread

from Modulo.Atomic import Waiter
from Modulo.Exceptions import *


class Flash:
    INSTRUCT_READ_PAGE = 0x10
    INSTRUCT_READ_INTERVAL = 0x11
    INSTRUCT_READ_INTO_FILE = 0x12
    INSTRUCT_WRITE_PAGE = 0x20
    INSTRUCT_WRITE_INTERVAL = 0x21
    INSTRUCT_WRITE_FROM_FILE = 0x22
    INSTRUCT_ERASE_PAGE = 0x30
    INSTRUCT_ERASE_INTERVAL = 0x32
    INSTRUCT_EXIT = 0xFF

    def __init__(self, ssd, from_queue: Queue[dict], fp: str):
        """
        创建虚拟 flash 并打开, 同时指定 flash 大小
        :param ssd: 打开 ssd 的路径
        :param from_queue: 来自 SSD 的分发通道
        :param fp: 创建的 flash 的路径, 如果 flash 已存在则直接打开
        """
        self.fp = fp if os.path.isabs(fp) else os.path.join(ssd.fp, fp)
        self.ssd = ssd
        self._queue = from_queue
        self.size = ssd.size // ssd.flashes  # ssd 保证可以整除
        self.pagesize = ssd.pagesize

        # 用于 pagesize 相关快速计算
        self.__page_mask = self.pagesize - 1
        self.__page_bits = self.__count_bits(self.pagesize)
        self.__page_tot = self.size >> self.__page_bits

        # 处理内存占用过高问题
        self.__bytes_limit = 1 << 30 >> self.__count_bits(self.ssd.flashes)
        self.__page_limit = self.__bytes_limit >> self.__page_bits

        # os.chdir(ssd.fp)
        if not os.path.exists(self.fp):
            self.__init_flash()

        self.file = open(self.fp, "rb+")

        self.__instruct = {
            self.INSTRUCT_READ_PAGE: self.__read,
            self.INSTRUCT_READ_INTO_FILE: self.__read_to_file,
            self.INSTRUCT_READ_INTERVAL: self.__read_pages,
            self.INSTRUCT_WRITE_PAGE: self.__write,
            self.INSTRUCT_WRITE_FROM_FILE: self.__write_from_file,
            self.INSTRUCT_WRITE_INTERVAL: self.__write_pages,
            self.INSTRUCT_ERASE_PAGE: self.__erase,
            self.INSTRUCT_ERASE_INTERVAL: self.__erase_pages,
        }

        self.__waiter = Waiter()
        self.listener()

    def execute(self, **msg) -> None:
        """执行线程"""
        _receiver = msg.get("receiver")
        _data = self.__instruct.get(
            msg.get("instruct"),
            lambda *args, **kwargs: None
        )(
            *msg.get("args", ()),
            **msg.get("kwargs", {})
        )
        if isinstance(_receiver, Waiter):
            _receiver.dec()
        elif isinstance(_receiver, Queue):
            _receiver.put(_data)
        self.__waiter.dec()

    def listener(self) -> None:
        """监听程序. 处理来自 SSD 的 flash 调用请求"""
        while True:
            _msg = self._queue.get()
            # 通信协议: dict{"instruct"=INSTRUCT_EXIT, "receiver"=None, "args"=(), "kwargs"={}}
            if _msg.get("instruct", self.INSTRUCT_EXIT) == self.INSTRUCT_EXIT:
                self.close()
                _receiver = _msg.get("receiver")
                if isinstance(_receiver, Waiter):
                    _receiver.dec()
                elif isinstance(_receiver, Queue):
                    _receiver.put(None)
                return
            self.__waiter.inc()
            _thread = Thread(target=self.execute, kwargs=_msg)
            _thread.start()

    def close(self):
        """关闭 flash"""
        self.__waiter.wait()
        self.file.close()

    def __init_flash(self):
        """创建 flash"""
        with open(self.fp, "wb") as _file:
            _rest = self.size
            while _rest > self.__bytes_limit:
                _file.write(self.__bytes_resize(b"", self.__bytes_limit))
                _rest -= self.__bytes_limit
            _file.write(self.__bytes_resize(b"", _rest))

    def __read(self, pageno: int) -> bytes:
        """
        读取单一页
        :param pageno: 页索引
        :return: 返回 bytes
        """
        if pageno < 0 or pageno >= self.__page_tot:
            raise OutOfBoundError("Access out of bounds: pageno [{}, {})".format(pageno, pageno + 1))
        self.file.seek(pageno << self.__page_bits, 0)
        return self.file.read(self.pagesize)

    def __read_pages(self, pageno: int, pages: int) -> bytes:
        """
        读取连续页
        :param pageno: 起始页索引
        :param pages: 页数
        :return: 返回 bytes
        """
        pages = max(pages, 0)
        if pageno < 0 or pageno + pages > self.__page_tot:
            raise OutOfBoundError("Access out of bounds: pageno [{}, {})".format(pageno, pageno + pages))
        self.file.seek(pageno << self.__page_bits, 0)
        return self.file.read(pages << self.__page_bits)

    def __read_to_file(self, pageno: int, pages: int, fp: str, sk: int) -> None:
        """
        读取单一页, 输出文件
        :param pageno: 页索引
        :param pages: 页数
        :param fp: 输出文件
        :param sk: 文件偏移
        """
        with open(fp, "rb+") as _file:
            _file.seek(sk, 0)
            # 避免一次读入内存过多
            while pages > self.__page_limit:
                _file.write(self.__read_pages(pageno, self.__page_limit))
                pageno += self.__page_limit
                pages -= self.__page_limit
            _file.write(self.__read_pages(pageno, pages))
            # for i in range(pages):
            #     _file.seek(sk + (i * self.ssd.flashes << self.__page_bits), 0)
            #     _file.write(self.__read(pageno + i))
            #     # _file.seek(self.ssd.flashes << self.__page_bits, 1)

    def __write(self, data: bytes, pageno: int) -> None:
        """
        覆盖单一页, 自动截断
        :param data: 写入页
        :param pageno: 页索引
        """
        if pageno < 0 or pageno >= self.__page_tot:
            raise OutOfBoundError("Access out of bounds: pageno [{}, {})".format(pageno, pageno + 1))
        self.file.seek(pageno << self.__page_bits, 0)
        self.file.write(self.__bytes_resize(data, self.pagesize))

    def __write_pages(self, data: bytes, pageno: int) -> None:
        """
        覆盖连续页, 自动对齐
        :param data: 写入流
        :param pageno: 起始页索引
        """
        if (pageno << self.__page_bits) + len(data) >= self.size:
            raise OutOfBoundError("Access out of bounds.")
        if len(data) & self.__page_mask:
            data += b"\x00" * (self.pagesize - (len(data) & self.__page_mask))
        self.file.seek(pageno << self.__page_bits, 0)
        self.file.write(self.__bytes_resize(
            data, len(data) + self.pagesize - 1 >> self.__page_bits << self.__page_bits
        ))

    def __write_from_file(self, fp: str, sk: int, pageno: int, pages: int) -> None:
        """
        覆盖单一页, 来自文件
        :param fp: 读取文件
        :param sk: 文件偏移
        :param pageno: 页索引
        :param pages: 页数
        """
        with open(fp, "rb") as _file:
            _file.seek(sk, 0)
            # 避免一次读入内存过多
            while pages > self.__page_limit:
                self.__write_pages(_file.read(self.__bytes_limit), pageno)
                pageno += self.__page_limit
                pages -= self.__page_limit
            self.__write_pages(_file.read(pages << self.__page_bits), pageno)
            # for i in range(pages):
            #     _file.seek(sk + (i * self.ssd.flashes << self.__page_bits), 0)
            #     self.__write(_file.read(self.pagesize), pageno + i)
            #     # _file.seek(self.ssd.flashes << self.__page_bits, 1)

    def __erase(self, pageno: int) -> None:
        """
        擦除单一页
        :param pageno:
        """
        self.__write(b"", pageno)

    def __erase_pages(self, pageno: int, pages: int) -> None:
        """
        擦除连续页
        :param pageno: 起始页索引
        :param pages: 页数
        """
        self.__write_pages(self.__bytes_resize(b"", pages << self.__page_bits), pageno)

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
