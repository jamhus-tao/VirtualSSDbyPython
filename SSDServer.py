import socket
import pickle
from threading import Thread
import os
from Modulo.SSD import SSD

PATH = "E:/VirtualSSD"


class Server:
    def __init__(self, _ssd, _path):
        self.__ssd = _ssd
        self.__path = _path
        # print(self.__path)

        _file_path = os.path.join(self.__path, "dict.bin")
        if os.path.exists(_file_path):
            with open(_file_path, "rb") as file:
                self.__Dict = pickle.loads(file.read())
                # print(Dict)
        else:
            self.__Dict = {}

        self.__start_server()

    def __start_server(self):
        _host = "127.0.0.1"
        _port = 5555

        _server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _server_socket.bind((_host, _port))

        # 最多监听十个连接。
        _server_socket.listen(10)
        print(f"Server listening on {_host}:{_port}")

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

            if _message[-1][1] == 7:
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

        if _li[0] == 1:
            _address = self.__ssd.create(_li[2])
            self.__Dict[_address] = (_li[1], _li[2])
            _result = "创建成功"

        elif _li[0] == 2:
            try:
                self.__ssd.delete(_li[1])
                _result = "删除成功"
            except Exception as e:
                _result = "Error: " + str(e)

        elif _li[0] == 3:
            try:
                _result = self.__copy_in(_li[1])
            except Exception as e:
                _result = "Error: " + str(e)

        elif _li[0] == 4:
            try:
                _result = self.__copy_out(_li[1], _li[2])
            except Exception as e:
                _result = "Error: " + str(e)

        elif _li[0] == 5:
            _origin_list = self.__ssd.list()
            _result = "{:<20}{:<20}{:<20}\n".format("begin", "name", "size")
            for _address, __ in _origin_list:
                _result += "{:<20}{:<20}{:<20}\n".format(str(_address), self.__Dict[_address][0],
                                                         str(self.__Dict[_address][1]))

            if not _origin_list:
                _result += "(empty)\n"

        elif _li[0] == 7:
            self.__ssd.close()
            self.__write_dict()
            _client_socket.send(pickle.dumps("服务端已关闭"))
            _client_socket.close()
            return

        else:
            _result = "未知指令"

        # 发送结果给客户端
        _client_socket.send(pickle.dumps(_result))
        _client_socket.close()
        return

    def __copy_in(self, _fp):
        _size = os.stat(_fp).st_size
        _address = self.__ssd.create(_size)
        self.__ssd.copy_in(_fp, _address)
        self.__Dict[_address] = (os.path.basename(_fp), _size)
        # print(os.path.basename(_fp))
        return "复制成功"

    def __copy_out(self, _address, _fp):
        self.__ssd.copy_out(_address, os.path.join(_fp, self.__Dict[_address][0]), self.__Dict[_address][1])
        return "复制成功"

    def __write_dict(self):
        if not os.path.exists(self.__path):
            os.mkdir(self.__path)

        _file_path = os.path.join(self.__path, "dict.bin")
        with open(_file_path, "wb") as w_file:
            w_file.write(pickle.dumps(self.__Dict))


if __name__ == "__main__":
    ssd = SSD(PATH, (64 << 30), 8, (4 << 10))
    Server(ssd, PATH)
