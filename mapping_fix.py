from Modulo.SSD import SSD

if __name__ == "__main__":
    ssd = SSD("E:/", (64 << 30), 8, (4 << 10))
    ssd._mapping._init_mapping()
    ssd._mapping._load_mapping()
    ssd.close()
