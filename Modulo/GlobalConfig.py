import os
import yaml

from Modulo import IO


class Configer:
    def __init__(self, fp: str = "Server.yml"):
        self.fp = fp
        if not os.path.exists(fp):
            raise AttributeError("Config YAML file not fount: {}".format(self.fp))
        with open(fp, "r", encoding="utf-8") as _file:
            _data = yaml.safe_load(_file)
        try:
            self.PATH = _data["ssd"]["fp"]
            self.SIZE = IO.parse_size(_data["ssd"]["size"])
            self.FLASHES = IO.parse_size(_data["ssd"].get("flashes", 8))
            self.PAGESIZE = IO.parse_size(_data["ssd"].get("pagesize", 4096))
            self.HOST = _data["server"]["host"]
            self.PORT = _data["server"]["port"]
            self.DICT = _data.get("filesys", {}).get("dict", "dict.bin")
        except KeyError:
            raise AttributeError("Necessary config missing")
        except ValueError:
            raise AttributeError("Cannot parse the config")
