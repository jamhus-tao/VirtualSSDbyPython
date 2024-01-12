import atexit
import time
from threading import Thread

class Node:
    def __init__(self):
        print("Node init")
        atexit.register(self.cleanup)

    def cleanup(self):
        print("脚本结束时执行的代码")


def main():
    print("线程调用")
    a = Node()


if __name__ == '__main__':
    print("主函数")
    client_handler = Thread(target=main)
    client_handler.start()
    # time.sleep(10)
    input()