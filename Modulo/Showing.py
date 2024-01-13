import matplotlib.patches as mpathes
from Modulo.Mapping import Mapping
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class Showing:
    def __init__(self, mapping: Mapping):
        self.mapping = mapping
        plt.rcParams["font.family"] = "FangSong"  # 支持中文显示
        self.fig = plt.figure(figsize=(5, 5))
        self.ax = self.fig.add_subplot(1, 1, 1)
        plt.gca().axes.get_xaxis().set_visible(False)  # x 轴不可见

    def update(self, _):
        plt.cla()  # 清空原有内容
        fig_size_width_length, fig_size_width = (1, 1)
        row = self.mapping.ssd.flashes
        line_length = self.mapping.address_tot // row
        plt.tick_params(top=False, bottom=False, left=False, right=False)
        names = ['flash[' + str(i) + ']' for i in reversed(range(row))]
        plt.yticks([i * 1 / (row * 3) for i in range(1, row * 3, 3)], names, fontsize=9)  # Y轴标签
        rect = mpathes.Rectangle(
            np.array([0, 0]),
            fig_size_width_length,
            fig_size_width,
            color="g",
            alpha=0.6
        )
        self.ax.add_patch(rect)
        for st, values in self.mapping.free_address_block.items():
            #print(st,values)
            lleft = st // row
            rright = (st + values - 1) // row
            for i in range(row):
                if lleft * row + i < st:
                    be = lleft + 1
                else:
                    be = lleft
                if rright * row + i > st + values - 1:
                    ed = rright - 1
                else:
                    ed = rright
                length = ed - be + 1
                if length == 0:
                    continue
                rect = mpathes.Rectangle(
                    np.array([
                        be / line_length * fig_size_width_length,
                        (row - i - 1) / row * fig_size_width
                    ]),
                    length / line_length * fig_size_width_length,
                    fig_size_width / row,
                    color="gray",
                    alpha=1
                )
                self.ax.add_patch(rect)
        for i in range(row):
            rect = mpathes.Rectangle(
                np.array([
                    0,
                    (row - i - 1) / row * fig_size_width
                ]),
                fig_size_width_length,
                fig_size_width / row,
                fill=None,
                linewidth=1
            )
            self.ax.add_patch(rect)

        self.fig.canvas.draw()

    def work(self, interval: int = 300):
        # plt.axis('off')
        _ani = FuncAnimation(
            self.fig,
            self.update,
            frames=100,
            interval=interval,
            blit=False,
            repeat=True
        )  # 创建动画效果
        # plt.grid()
        plt.show()
