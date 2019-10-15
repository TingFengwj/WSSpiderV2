# -*- coding: utf-8 -*-

# Scrapy settings for WSSpiderV2 project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import redis, os
from WSSpiderV2.configs.develop import *

BOT_NAME = 'WSSpiderV2'

SPIDER_MODULES = ['WSSpiderV2.spiders']
NEWSPIDER_MODULE = 'WSSpiderV2.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'WSSpiderV2 (+http://www.yourdomain.com)'

REDIS_URL = 'redis://%s:%d' % (REDIS_CONFIG.get('host'), REDIS_CONFIG.get('port'))
REDIS_PARAMS = {'db': REDIS_CONFIG.get('db')}

SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
REDIS_START_URLS_KEY = REDIS_KEY
REDIS_ARTICLE_LIST_KEY = 'article_list'
REDIS_ARTICLE_CACHE_KEY = 'article_list_cache:'
REDIS_SPIDER_ERROR_LIST_KEY = 'spider_error_list'
# Obey robots.txt rules
ROBOTSTXT_OBEY = False
HTTPERROR_ALLOWED_CODES = [403]
# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 32
COOKIES_ENABLED = False
# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'WSSpiderV2.middlewares.Wsspiderv2SpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   'WSSpiderV2.middlewares.UserAgentDownloadMiddleware': 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'WSSpiderV2.pipelines.Wsspiderv2Pipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# HTTP：启用HTTP缓存，是否针对所有的请求进行本地数据的缓存，默认是禁用的。开启时，数据会优先从本地缓存中读取，爬取速度会快一些。
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
REDIS_CONFIG = REDIS_CONFIG
redis_pool = redis.ConnectionPool(**REDIS_CONFIG)
client = redis.Redis(connection_pool=redis_pool)

# LOG_ENABLED = False  # 关闭日志

HTTP_HEADER = HTTP_HEADER

BASE_LOG_DIR = os.path.join(BASE_DIR, "log")
if not os.path.isdir(BASE_LOG_DIR):
    os.mkdir(BASE_LOG_DIR)
BASE_INFO_DIR = os.path.join(BASE_LOG_DIR, 'info_log')
if not os.path.isdir(BASE_INFO_DIR):
    os.mkdir(BASE_INFO_DIR)
BASE_ERROR_DIR = os.path.join(BASE_LOG_DIR, 'error_log')
if not os.path.isdir(BASE_ERROR_DIR):
    os.mkdir(BASE_ERROR_DIR)
LOGGING = {
    'version': 1,  # 保留字
    'disable_existing_loggers': False,  # 禁用已经存在的logger实例
    # 日志文件的格式
    'formatters': {
        # 详细的日志格式
        'standard': {
            'format': '%(asctime)s%(levelname)s[%(threadName)s:%(thread)d][task_id:%(name)s][%(filename)s:%(lineno)d]'
                      '%(message)s'
        },
        # 简单的日志格式
        'simple': {
            'format': '%(asctime)s[%(levelname)s][%(filename)s:%(lineno)d]%(message)s'
        },
        # 定义一个特殊的日志格式
        'collect': {
            'format': '%(asctime)s：%(message)s'
        }
    },
    # 处理器
    'handlers': {
        # 默认的
        'info': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',  # 保存到文件，自动切
            'filename': os.path.join(BASE_INFO_DIR, "info.log"),
            # 'maxBytes': 1024 * 1024 * 50,  # 日志大小 50M
            'interval': 1,
            'when': 'MIDNIGHT',
            'backupCount': 15,
            'delay': True,
            'formatter': 'standard',
            'encoding': "utf-8"
        },
        # 专门用来记错误日志
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',  # 保存到文件，自动切
            'filename': os.path.join(BASE_ERROR_DIR, "error.log"),
            # 'maxBytes': 1024 * 1024 * 50,  # 日志大小 50M
            'interval': 1,
            'when': 'MIDNIGHT',
            'backupCount': 15,
            'delay': True,
            'formatter': 'standard',
            'encoding': "utf-8"
        },
    },
    # 记录器
    'loggers': {
        'spider': {
            'handlers': ['info', 'error'],
            'level': 'DEBUG',
            'propagate': False,  # 向不向更高级别的logger传递
        }
    },
}
