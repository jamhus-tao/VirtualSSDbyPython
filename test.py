from Modulo.SSD import SSD


if __name__ == "__main__":
    ssd = SSD("E:/", (64 << 30), 8, (4 << 10))
    ssd.close()
