import json

class Json:
    """json 파일 제어"""
    
    def __init__(self, path, encoding="UTF8"):
        self.path = path
        self.encoding = encoding

    def read(self):
        """데이터 읽기"""
        with open(self.path, "r", encoding=self.encoding) as file:
            return json.load(file)

    def write(self, object):
        """ 기존 데이터 삭제, 새 데이터 쓰기"""
        with open(self.path, "w", encoding=self.encoding) as file:
            json.dump(object, file, indent=4)

    def append(self, keypath, value):
        """(미완성) 기존 데이터 유지, 새 데이터 쓰기"""
        pass

    def delete(self, keypath):
        """(미완성) 데이터 삭제"""
        pass


if __name__ == "__main__":
    import pprint
    import datetime
    import random
    import time

    js = Json("./file/test.json")
    count = 0
    start = time.time()
    while count < 10:

        dict = {}
        dict["measurement"] = "meas_test"
        dict["tags"] = {}
        dict["fields"] = {}
        now = time.strftime("%Y.%m.%d %H:%M:%S")

        for i in range(0,10000):
            tag_name = "tag_name_{}".format(i)
            dict[tag_name] = [i, now, "good"]
        
        js.write(dict)
        js.read()
        count += 1
        print(count)

    print(time.time()-start)
