import matplotlib.patches as mpathes
from Modulo import Mapping
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from threading import Thread, Event

class showing:
    def __init__(self, Mapping1:Mapping.Mapping):
        self.Mapping1=Mapping1
        plt.rcParams["font.family"] = "FangSong"  # 支持中文显示
        self.fig= plt.figure(figsize=(5,5))
        self.ax = self.fig.add_subplot(1, 1, 1)
        plt.gca().axes.get_xaxis().set_visible(False)# x 轴不可见

    def update(self, frame):
        plt.cla()  # 清空原有内容
        figsizewidlength,figsizewidth=(1,1)
        row=self.Mapping1.flash
        linelength=self.Mapping1.address_len
        plt.tick_params(top=False,bottom=False,left=False,right=False)
        names=['flash[' + str(i) + ']' for i in reversed(range(row))]
        plt.yticks([i*1/(row*3)for i in range(1,row*3,3)], names )  # Y轴标签
        rect = mpathes.Rectangle(np.array([0,0]),figsizewidlength,figsizewidth,color="g",alpha=0.6)
        self.ax.add_patch(rect)
        for st,values in self.Mapping1.free_address_block.items():
            #print(st,values)
            lleft=(st)//row
            rright=(st+values-1)//row
            for i in range(row):
                if((lleft)*row+i<st):be=lleft+1
                else:be=lleft
                if((rright)*row+i>st+values-1):ed=rright-1
                else:ed=rright
                length=ed-be+1
                if(length==0):continue
                rect = mpathes.Rectangle(np.array([be/linelength*figsizewidlength,(row-i-1)/row*figsizewidth]),length/linelength*figsizewidlength,figsizewidth/row,color="gray",alpha=1)
                self.ax.add_patch(rect)
        for i in range(row):
            rect = mpathes.Rectangle(np.array([0,(row-i-1)/row*figsizewidth]),figsizewidlength,figsizewidth/row, fill=None, linewidth=1)
            self.ax.add_patch(rect)

        self.fig.canvas.draw()
    def work(self):
        #plt.axis('off')
        ani = FuncAnimation(self.fig, self.update, frames=100, interval=3000, blit=False, repeat=False)  # 创建动画效果
        plt.grid()
        plt.show()
