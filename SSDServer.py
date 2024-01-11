import socket
import pickle
from threading import Thread
import os
import time
from Modulo.SSD import SSD

client_handler_queue = []


def copy_in(fp):
    address = ssd.create(os.stat(fp).st_size)
    ssd.copy_in(fp, address)
    return "success"


def work(li, client_socket):

    result = "Unknown Error"
    if li[0] == 1:
        address = ssd.create(li[2])
        Dict[address] = li[1]
        result = "创建成功"

    elif li[0] == 2:
        try:
            ssd.delete(li[1])
            result = "success"
        except Exception as e:
            result = "Error: " + str(e)

    elif li[0] == 3:
        try:
            result = copy_in(li[1])
        except Exception as e:
            result = "Error: " + str(e)

    elif li[0] == 4:
        pass

    elif li[0] == 5:
        result = ssd.list()

    elif li[0] == 7:
        client_socket.send(pickle.dumps("已发出关闭指令"))
        client_socket.close()
        return

    else:
        result = "未知指令"

    # 发送结果给客户端
    client_socket.send(pickle.dumps(result))
    client_socket.close()
    return


def start_server():
    host = "127.0.0.1"
    port = 5555

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))

    # 最多监听十个连接。
    server_socket.listen(10)

    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address}")

        li = client_socket.recv(1024)
        if not li:
            continue

        li = pickle.loads(li)

        client_handler = Thread(target=work, args=(li, client_socket))
        client_handler_queue.append(client_handler)
        client_handler.start()

        if li[0] == 7:
            for client_handler in client_handler_queue:
                client_handler.join()

            return


if __name__ == "__main__":
    path = os.path.abspath("data")
    # print(path)

    if os.path.exists(os.path.join(path, "dict.bin")):
        with open(path + "\\dict.bin", "rb") as file:
            Dict = pickle.loads(file.read())
            print(Dict)
    else:
        Dict = {}

    ssd = SSD("E:/VirtualSSD", (64 << 30), 8, (4 << 10))
    start_server()
    ssd.close()

    with open(path + "\\dict.bin", "wb") as file:
        file.write(pickle.dumps(Dict))
