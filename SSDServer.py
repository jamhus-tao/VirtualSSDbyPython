import os
import socket
import pickle
from threading import Thread
from datetime import datetime

from Modulo.GlobalConfig import Configer
from Modulo.SSD import SSD
from Modulo.Showing import Showing
from Modulo import IO


class Server:
    def __init__(self, ssd: SSD, cfg: Configer):
        self.__ssd = ssd
        self.__cfg = cfg
        # print(self.__path)

        _file_path = os.path.join(self.__cfg.PATH, self.__cfg.DICT)
        if os.path.exists(_file_path):
            with open(_file_path, "rb") as file:
                self.__Dict = pickle.loads(file.read())
                # print(Dict)
        else:
            self.__Dict = {}

        self.__start_server()

    def __start_server(self):
        # _host = "127.0.0.1"
        # _port = 5555

        _server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _server_socket.bind((self.__cfg.HOST, self.__cfg.PORT))

        # 最多监听十个连接。
        _server_socket.listen(10)
        print(f"Server listening on {self.__cfg.HOST}:{self.__cfg.PORT}")

        _message = [(0, 0)]
        _cnt = 0

        self.__client_handler_pool = []
        while True:
            _client_socket, _client_address = _server_socket.accept()
            print(f"Accepted connection from {_client_address}")

            _cnt = _cnt + 1
            _client_handler = Thread(target=self.__work, args=(_client_socket, _message, _cnt))
            self.__client_handler_pool.append(_client_handler)
            _client_handler.start()

            while _message[-1][0] != _cnt:
                continue

            if _message[-1][1] == 8:
                for _client_handler in self.__client_handler_pool:
                    _client_handler.join()

                return

    def __work(self, _client_socket, _message, _cnt):
        _li = _client_socket.recv(1024)

        # 建立连接后，如果客户端在发送信息之前的一瞬间被关闭，则会得到一个空的 li
        if not _li:
            _message.append((_cnt, 0))
            return

        _li = pickle.loads(_li)
        _message.append((_cnt, _li[0]))

        _result = "Unknown Error"
        if _li[0] == 1:
            _origin_list = self.__ssd.list()
            _result = "{:<20}{:<20}{:<20}{:<30}{}\n".format("begin", "name", "size", "modified date", "notes")
            for _address, __ in _origin_list:
                _result += "{:<20}{:<20}{:<20}{:<30}{}\n".format(
                    str(_address),
                    self.__Dict[_address][0],
                    IO.to_humanized_size(self.__Dict[_address][1]),
                    # str(self.__Dict[_address][1]),
                    str(self.__Dict[_address][2]).split(".")[0],
                    self.__Dict[_address][3]
                )

            if not _origin_list:
                _result += "(empty)\n"

        elif _li[0] == 2:
            try:
                _address = self.__ssd.create(_li[2])
                self.__Dict[_address] = (_li[1], _li[2], datetime.now(), _li[3])
                _result = "创建成功"
            except Exception as e:
                _result = "Error: " + str(e)

        elif _li[0] == 3:
            try:
                self.__ssd.delete(_li[1])
                _result = "删除成功"
            except Exception as e:
                _result = "Error: " + str(e)

        elif _li[0] == 4:
            try:
                _result = self.__copy_in(_li[1], _li[2])
            except Exception as e:
                _result = "Error: " + str(e)

        elif _li[0] == 5:
            try:
                _result = self.__copy_out(_li[1], _li[2])
            except Exception as e:
                _result = "Error: " + str(e)

        elif _li[0] == 6:
            _origin_list = self.__ssd.list()
            for _address, __ in _origin_list:
                self.__ssd.delete(_address)

            self.__Dict = {}
            _result = "SSD 已格式化"

        elif _li[0] == 8:
            self.__ssd.close()
            self.__write_dict()
            _client_socket.send(pickle.dumps("SSD 已关闭"))
            _client_socket.close()
            return

        else:
            _result = "未知指令"

        # 发送结果给客户端
        _client_socket.send(pickle.dumps(_result))
        _client_socket.close()
        return

    def __copy_in(self, _fp, _notes):
        _size = os.stat(_fp).st_size
        _address = self.__ssd.create(_size)
        self.__ssd.copy_in(_fp, _address)
        self.__Dict[_address] = (os.path.basename(_fp), _size, datetime.now(), _notes)
        # print(os.path.basename(_fp))
        return f"复制成功，文件 {_fp} 已写入 SSD中"

    def __copy_out(self, _address, _fp):
        self.__ssd.copy_out(_address, os.path.join(_fp, self.__Dict[_address][0]), self.__Dict[_address][1])
        return f"复制成功，已写入 {_fp}"

    def __write_dict(self):
        if not os.path.exists(self.__cfg.PATH):
            os.mkdir(self.__cfg.PATH)

        _file_path = os.path.join(self.__cfg.PATH, self.__cfg.DICT)
        with open(_file_path, "wb") as w_file:
            w_file.write(pickle.dumps(self.__Dict))


if __name__ == "__main__":
    cfg = Configer()
    ssd = SSD(cfg.PATH, cfg.SIZE, cfg.FLASHES, cfg.PAGESIZE)
    server_handler = Thread(target=Server, args=(ssd, cfg))
    server_handler.start()
    showing_handler = Showing(ssd._mapping)
    showing_handler.work(cfg.FLUSH_INTERVAL)
    server_handler.join()
