import socket
import pickle
import time
from Modulo import IO
import os


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

    if not p:
        return True

    close = False
    try:
        p = int(p)
        if p == 1:
            send_message = pickle.dumps([1])

        elif p == 2:
            name = input("请输入新建文件的文件名：\n> ")
            size = IO.input_humanized_size("请输入新建文件的大小：\n> ")
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
            try:
                if li[3] == "-m":
                    notes = li[4]
                else:
                    print("未知指令")
                    return True
            except IndexError:
                notes = ""

            try:
                li[1], li[2]
            except IndexError:
                print("非法输入，参数输入不足")
                return True

            if IO.is_int(li[2]):
                li[2] = int(li[2])
            elif IO.is_humanized_size(li[2]):
                li[2] = IO.parse_humanized_size(li[2])
            else:
                print("非法输入，第三个参数无法识别")
                return True

            send_message = pickle.dumps([2, li[1], li[2], notes])

        elif li[0] == "del":
            try:
                send_message = pickle.dumps([3, int(li[1])])
            except ValueError:
                print("非法输入，第二个参数应该是一个整数")
                return True
            except IndexError:
                print("非法输入，参数输入不足")
                return True

        elif li[0] == "cp":
            notes = ""
            has_notes = False
            fp = ""
            has_fp = False
            address = -1
            visited = {0}
            for i in range(1, len(li)):
                if li[i] == "-m" and not has_notes:
                    try:
                        notes = li[i + 1]
                        visited.add(i)
                        visited.add(i + 1)
                        has_notes = True
                        continue
                    except IndexError:
                        print("非法输入，-m 后面未输入备注")
                        return True

                if has_fp:
                    continue

                temp = li[i]
                if li[i] == "\"":
                    print("非法输入")
                    return True

                if len(li[i]) >= 2 and temp[0] == "\"" and temp[-1] == "\"":
                    temp = temp[1:-1]

                temp = os.path.abspath(temp)
                if os.path.exists(temp):
                    fp = temp
                    visited.add(i)
                    has_fp = True

            if len(visited) == len(li):
                if fp == "":
                    print("非法输入")
                    return True

                if os.path.isdir(fp):
                    print(f"不可以是个文件夹: {fp}")
                    return True

                send_message = pickle.dumps([4, fp, notes])

            elif len(visited) >= 2 and len(visited) + 1 == len(li):
                for i in range(len(li)):
                    if i not in visited:
                        address = int(li[i])
                        break

                if fp == "" or address == -1:
                    print("非法输入")
                    return True

                if not os.path.isdir(fp):
                    print(f"不是个文件夹: {fp}")
                    return True

                send_message = pickle.dumps([5, address, fp, notes])

            else:
                print("非法输入")
                return True

        elif li[0] == "format":
            send_message = pickle.dumps([6])

        elif li[0] == "exit":
            return False

        elif li[0] == "close":
            send_message = pickle.dumps([8])
            close = True

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
    IO.to_humanized_size(6)
    while send_request():
        pass
