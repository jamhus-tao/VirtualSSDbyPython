import os
from Modulo.GlobalConfig import Configer
from Modulo.SSD import SSD


if __name__ == "__main__":
    cfg = Configer()
    ssd = SSD(cfg.PATH, (64 << 30), 8, (4 << 10))
    ssd._mapping._init_mapping()
    ssd._mapping.close = lambda: None
    if os.path.exists(os.path.join(cfg.PATH, cfg.DICT)):
        os.remove(os.path.join(cfg.PATH, cfg.DICT))
    ssd.close()
