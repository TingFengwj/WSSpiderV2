# -*- coding: utf-8 -*-
from hashlib import md5

from hashlib import md5


class SimpleHash(object):
    def __init__(self, cap, seed):
        self.cap = cap
        self.seed = seed

    def hash(self, value):
        ret = 0
        for i in range(len(value)):
            ret += self.seed * ret + ord(value[i])
        return (self.cap - 1) & ret


class BloomFilter(object):
    def __init__(self, blockNum=1, key=None):
        """
        :param blockNum: one blockNum for about 90,000,000; if you have more strings for filtering, increase it.
        :param key: the key's name in Redis
        """
        self.server = None
        self.bit_size = 1 << 31
        # Redis的String类型最大容量为512M，现使用256M
        self.seeds = [5, 7, 11]
        self.key = key
        self.blockNum = blockNum
        self.hashfunc = []
        for seed in self.seeds:
            self.hashfunc.append(SimpleHash(self.bit_size, seed))

    def isContains(self, str_input):
        if not str_input:
            return False
        m5 = md5()
        m5.update(str_input.encode("utf8"))
        str_input = m5.hexdigest()
        ret = True
        for f in self.hashfunc:
            loc = f.hash(str_input)
            ret = ret & self.server.getbit(self.key, loc)
        return ret

    def insert(self, str_input):
        m5 = md5()
        m5.update(str_input.encode("utf8"))
        str_input = m5.hexdigest()
        for f in self.hashfunc:
            loc = f.hash(str_input)
            self.server.setbit(self.key, loc, 1)


if __name__ == '__main__':
    content = ''
    bl = BloomFilter(key='monitor_project')
    if not bl.isContains(content):
        bl.insert(content)
    else:
        pass
