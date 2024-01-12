import os
import yaml
from Modulo.SSD import SSD


class Configer:
    def __init__(self, fp: str = "Server.yml"):
        self.fp = fp
        if not os.path.exists(fp):
            raise AttributeError("Config YAML file not fount: {}".format(self.fp))
        with open(fp, "r") as _file:
            _data = yaml.safe_load(_file)
        try:
            self.PATH = _data["ssd"]
            self.HOST = _data["host"]
            self.PORT = _data["port"]
            self.DICT = _data.get("dict", "dict.bin")
        except KeyError:
            raise AttributeError("Necessary config missing")


if __name__ == "__main__":
    cfg = Configer()
    ssd = SSD(cfg.PATH, (64 << 30), 8, (4 << 10))
    ssd._mapping._init_mapping()
    ssd._mapping._load_mapping()
    os.remove(os.path.join(cfg.PATH, cfg.DICT))
    ssd.close()
