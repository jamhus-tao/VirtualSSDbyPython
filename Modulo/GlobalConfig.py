import os
import yaml


class Configer:
    __BITS = {
        "B": 0,  "K": 10, "M": 20,
        "G": 30, "T": 40, "P": 50,
        "E": 60, "Z": 70, "Y": 80,
    }

    def __init__(self, fp: str = "Server.yml"):
        self.fp = fp
        if not os.path.exists(fp):
            raise AttributeError("Config YAML file not fount: {}".format(self.fp))
        with open(fp, "r", encoding="utf-8") as _file:
            _data = yaml.safe_load(_file)
        try:
            self.PATH = _data["ssd"]["fp"]
            self.SIZE = self.__parse_size(_data["ssd"]["size"])
            self.FLASHES = self.__parse_size(_data["ssd"].get("flashes", 8))
            self.PAGESIZE = self.__parse_size(_data["ssd"].get("pagesize", 4096))
            self.HOST = _data["server"]["host"]
            self.PORT = _data["server"]["port"]
            self.DICT = _data.get("filesys", {}).get("dict", "dict.bin")
        except KeyError:
            raise AttributeError("Necessary config missing")
        except ValueError:
            raise AttributeError("Cannot parse the config")

    @staticmethod
    def __parse_size(s) -> int:
        """解析文件大小字符串， 返回单位 Bytes 的大小"""
        if isinstance(s, int):
            return s
        if isinstance(s, float):
            return int(s)
        s = str(s).upper()
        _i = len(s) - 1
        _bits = 0
        while _i >= 0 and s[_i] in Configer.__BITS:
            _bits += Configer.__BITS[s[_i]]
            _i -= 1
        return int(float(s[:_i + 1])) << _bits
