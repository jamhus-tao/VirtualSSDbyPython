import socket
import pickle
import time
from Modulo import IO
# import os
# import sys


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
1. 查看 SSD 使用情况
2. 新建文件
3. 删除文件
4. 复制指定文件至 SSD 中
5. 复制 SSD 至指定文件夹
6. 格式化
7. 退出
8. 关闭服务端并退出
> """)

    close = False
    try:
        p = int(p)
        if p == 1:
            send_message = pickle.dumps([1])

        elif p == 2:
            name = input("请输入新建文件的文件名：\n> ")
            size = IO.input_int("请输入新建文件的大小：\n> ")
            notes = input("请输入新建文件的备注：\n> ")

            send_message = pickle.dumps([2, name, size, notes])

        elif p == 3:
            address = IO.input_int("请输入删除的起始地址：\n> ")

            send_message = pickle.dumps([3, address])

        elif p == 4:
            fp = IO.input_file("请输入被拷贝文件的路径：\n> ")

            notes = input("请输入新建文件的备注：\n> ")

            send_message = pickle.dumps([4, fp, notes])

        elif p == 5:
            address = IO.input_int("请输入 SSD 中被拷贝文件的起始地址：\n> ")
            fp = IO.input_folder("请输入拷出文件夹的路径：\n> ")

            send_message = pickle.dumps([5, address, fp])

        elif p == 6:
            send_message = pickle.dumps([6])

        elif p == 7:
            return False

        elif p == 8:
            send_message = pickle.dumps([8])
            close = True

        else:
            print("未知指令")
            return True

    except ValueError:
        li = p.split()
        # print(li)
        if li[0] == "ls":
            send_message = pickle.dumps([1])

        elif li[0] == "new":
            notes = input("请输入新建文件的备注：\n> ")

            return pickle.dumps([2, li[1], li[2], notes])

        elif li[0] == "del":
            send_message = pickle.dumps([3, li[1]])

        elif li[0] == "cp":
            try:
                if li[2] == "-m":
                    notes = li[3]
                else:
                    print("未知指令")
                    return True
            except IndexError:
                notes = ""

            send_message = pickle.dumps([4, li[1], notes])
        else:
            print("未知指令")
            return True

    condition, client_socket = connect(close)
    if not condition:
        if close:
            print("服务端已关闭")
            return False
        return True

    start_time = time.time()
    client_socket.send(send_message)

    # 接收服务器的响应
    response = client_socket.recv(1024)

    response = pickle.loads(response)
    end_time = time.time()

    print(response)
    print("操作共花费：{:.3} s".format(end_time - start_time), end="\n\n")

    client_socket.close()

    if close:
        return False
    return True


if __name__ == "__main__":
    # sys.stdin = open('in.txt', 'r')
    while send_request():
        pass
