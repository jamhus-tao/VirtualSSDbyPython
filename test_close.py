from datetime import datetime

if __name__ == '__main__':
    s = str(datetime.now()).split(".")[0]
    print(s)
