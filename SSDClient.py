import socket
import pickle
import os
import sys
import shutil


def send_request():
    host = "127.0.0.1"
    port = 5555

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            client_socket.connect((host, port))
            break
        except ConnectionRefusedError:
            s = input("连接失败，服务端未开启，输入任意键重试...")
            if s == "exit":
                return False

    p = input("""请选择操作：
1. 新建文件
2. 删除文件
3. 复制文件至硬盘
4. 复制硬盘文件至指定文件夹
5. 查看硬盘使用情况
6. 退出
7. 关闭服务端并退出
> """)
    if p == "1":
        name = input("请输入新建文件的文件名：\n> ")
        size = input("请输入新建文件的大小：\n> ")

        client_socket.send(pickle.dumps([1, name, size]))

    elif p == "2":
        address = int(input("请输入删除的起始地址：\n> "))
        client_socket.send(pickle.dumps([2, address]))

    elif p == "3":
        fp = input("请输入被拷贝文件的路径：\n> ")
        if fp[0] == "\"" and fp[-1] == "\"":
            fp = fp[1:-1]

        fp = os.path.abspath(fp)
        client_socket.send(pickle.dumps([3, fp]))

    elif p == "4":
        client_socket.send(pickle.dumps([4]))

    elif p == "5":
        client_socket.send(pickle.dumps([5]))

    elif p == "6":
        client_socket.close()
        return False

    elif p == "7":
        client_socket.send(pickle.dumps([7]))
        response = client_socket.recv(1024)
        response = pickle.loads(response)
        print(response)
        client_socket.close()
        return False

    else:
        client_socket.send(pickle.dumps("未知指令"))

    # 接收服务器的响应
    response = client_socket.recv(1024)

    response = pickle.loads(response)

    print(response)

    client_socket.close()

    return True


if __name__ == "__main__":
    # sys.stdin = open('in.txt', 'r')
    while send_request():
        pass
