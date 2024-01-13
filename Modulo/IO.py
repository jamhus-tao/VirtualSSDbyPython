import os


def input_int(s: str = "") -> int:
    while True:
        _x = input(s)
        try:
            _x = int(_x)
            return _x
        except Exception as e:
            print(f"Error:{e},请重新输入")


def input_name(s: str = ""):
    fp = input(s)
    if fp == "\"":
        print("不是个文件名")
        return False, ""

    if len(fp) >= 2 and fp[0] == "\"" and fp[-1] == "\"":
        fp = fp[1:-1]

    fp = os.path.abspath(fp)
    return True, fp


def input_file(s: str = "") -> str:
    while True:
        p, fp = input_name(s)
        if not p:
            continue

        if not os.path.exists(fp):
            print(f"文件不存在: {fp}")
            continue

        if os.path.isdir(fp):
            print(f"不可以是个文件夹: {fp}")
            continue

        break

    return fp


def input_folder(s: str = "") -> str:
    while True:
        p, fp = input_name(s)
        if not p:
            continue

        if not os.path.exists(fp):
            print(f"文件夹不存在: {fp}")
            continue

        if not os.path.isdir(fp):
            print(f"不是个文件夹: {fp}")
            continue

        break

    return fp


__BITS = {
    "B": 0, "K": 10, "M": 20,
    "G": 30, "T": 40, "P": 50,
    "E": 60, "Z": 70, "Y": 80,
}


def parse_humanized_size(s) -> int:
    """解析人性化文件大小表达式, 返回单位为 Bytes"""
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


def to_humanized_size(i: int) -> str:
    """转换为人性化文件大小表达式"""
    raise NotImplementedError()


def parse_time_seconds(s) -> float:
    """解析以秒为单位的时间"""
    if isinstance(s, int) or isinstance(s, float):
        return s
    s = str(s).lower()
    if s.endswith("ns"):
        return float(s[:-2]) / 1e9
    if s.endswith("us"):
        return float(s[:-2]) / 1e6
    if s.endswith("ms"):
        return float(s[:-2]) / 1e3
    if s.endswith("s"):
        return float(s[:-1])
    return float(s)
