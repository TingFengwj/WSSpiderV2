# -*- coding: utf-8 -*-

DATABASES = {
    'host': '192.168.0.167',
    'database': 'wspider',
    'user': 'root',
    'password':  'QWE@zw666',
    'port': 3306,
    'charset': 'utf8mb4'
}

REDIS_CONFIG = {
    'host': '192.168.0.167',
    'port': 6379,
    'db': 0
}

REDIS_KEY = 'class_config'

MAX_PROCESSES = 8

BASE_DIR = '/home/spider/logs/'


HTTP_HEADER = [
    {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/"
                  "*;q=0.8,application/signed-exchange;v=b3",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                      "like Gecko) Chrome/77.0.3865.90 Safari/537.36"
    },
    {
        "Accept": "text/html,application/xhtml+xml,application/xml;",
        "Accept-Encoding": "gzip",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/42.0.2311.90 Safari/537.36"
    }
]

