import os


def input_int(s: str = "") -> int:
    while True:
        _x = input(s)
        try:
            _x = int(_x)
            return _x
        except Exception as e:
            print(f"Error:{e},请重新输入")


def input_file(s: str = "") -> str:
    while True:
        fp = input(s)
        if fp[0] == "\"" and fp[-1] == "\"":
            fp = fp[1:-1]

        fp = os.path.abspath(fp)
        if os.path.exists(fp):
            break
        else:
            print(f"文件不存在: {fp}")

    return fp


def input_folder(s: str = "") -> str:
    while True:
        fp = input(s)
        if fp[0] == "\"" and fp[-1] == "\"":
            fp = fp[1:-1]
        fp = os.path.abspath(fp)

        if not os.path.exists(fp):
            print(f"文件夹不存在: {fp}")
            continue

        if not os.path.isdir(fp):
            print(f"不是个文件夹: {fp}")
            continue

        break

    return fp


__BITS = {
    "B": 0,  "K": 10, "M": 20,
    "G": 30, "T": 40, "P": 50,
    "E": 60, "Z": 70, "Y": 80,
}


def parse_size(s) -> int:
    """解析文件大小字符串， 返回单位 Bytes 的大小"""
    if isinstance(s, int):
        return s
    if isinstance(s, float):
        return int(s)
    s = str(s).upper()
    _i = len(s) - 1
    _bits = 0
    while _i >= 0 and s[_i] in __BITS:
        _bits += __BITS[s[_i]]
        _i -= 1
    return int(float(s[:_i + 1])) << _bits
