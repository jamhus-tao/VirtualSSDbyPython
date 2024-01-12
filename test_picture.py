import time

import matplotlib.pyplot as plt
from threading import Thread


def serve():
    time.sleep(3)


if __name__ == '__main__':
    # 你的绘图代码
    plt.plot([1, 2, 3, 4], [10, 20, 25, 30])

    # 显示图形窗口
    plt.pause(1)
    plt.show(block=False)
    server_handler = Thread(target=serve)
    server_handler.start()

    server_handler.join()

    # 在某个地方调用以下方法来关闭图形窗口
    plt.close()
