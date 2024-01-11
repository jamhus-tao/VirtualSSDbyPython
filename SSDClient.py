import socket
import pickle
import os
import sys


class IO:
    @staticmethod
    def input_int(s: str = "") -> int:
        while True:
            _x = input(s)
            try:
                _x = int(_x)
                return _x
            except Exception as e:
                print(f"Error:{e},请重新输入")


def connect(close):
    host = "127.0.0.1"
    port = 5555

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
    except ConnectionRefusedError:
        if not close:
            print("连接失败，服务端未开启\n")
        return False, 0

    # while True:
    #     try:
    #         client_socket.send(pickle.dumps(""))
    #         break
    #     except ConnectionResetError:
    #         s = input("服务端已关闭，输入回车重试，输入 exit 退出\n> ")
    #         if s == "exit":
    #             return

    return True, client_socket


def send_request():
    p = input("""请选择操作：
1. 新建文件
2. 删除文件
3. 复制文件至硬盘
4. 复制硬盘文件至指定文件夹
5. 查看硬盘使用情况
6. 退出
7. 关闭服务端并退出
> """)

    close = False
    if p == "1":
        name = input("请输入新建文件的文件名：\n> ")
        size = IO.input_int("请输入新建文件的大小：\n> ")

        send_message = pickle.dumps([1, name, size])

    elif p == "2":
        address = IO.input_int("请输入删除的起始地址：\n> ")

        send_message = pickle.dumps([2, address])

    elif p == "3":
        fp = input("请输入被拷贝文件的路径：\n> ")
        if fp[0] == "\"" and fp[-1] == "\"":
            fp = fp[1:-1]

        fp = os.path.abspath(fp)

        send_message = pickle.dumps([3, fp])

    elif p == "4":
        address = IO.input_int("请输入硬盘中被拷贝文件的起始地址：\n> ")
        fp = input("请输入拷出文件夹的路径：\n> ")
        if fp[0] == "\"" and fp[-1] == "\"":
            fp = fp[1:-1]

        fp = os.path.abspath(fp)

        send_message = pickle.dumps([4, address, fp])

    elif p == "5":
        send_message = pickle.dumps([5])

    elif p == "6":
        return False

    elif p == "7":
        send_message = pickle.dumps([7])
        close = True

    else:
        send_message = pickle.dumps("未知指令")

    condition, client_socket = connect(close)
    if not condition:
        if close:
            print("服务端已关闭")
            return False
        return True

    client_socket.send(send_message)

    # 接收服务器的响应
    response = client_socket.recv(1024)

    response = pickle.loads(response)

    print(response)

    client_socket.close()

    if close:
        return False
    return True


if __name__ == "__main__":
    # sys.stdin = open('in.txt', 'r')
    while send_request():
        pass
