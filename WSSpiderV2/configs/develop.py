import pymysql, os

DATABASES = {
    'host': '192.168.0.167',
    # 'host': 'localhost',
    # 'database': 'wspider',
    'database': 'test_spiderv2',  # 测试库
    'user': 'root',
    'password': 'QWE@zw666',
    'port': 3306,
    # 'mincached': 5,
    # 'maxcached': 30,
    # 'maxusage': 30,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

REDIS_CONFIG = {
    'host': '192.168.0.167',
    'port': 6379,
    'db': 4
}

REDIS_KEY = 'wenjun'

MAX_PROCESSES = 16

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

HTTP_HEADER = {
    "Accept": "text/html,application/xhtml+xml,application/xml;",
    "Accept-Encoding": "gzip",
    "Accept-Language": "zh-CN,zh;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/42.0.2311.90 Safari/537.36"
}
