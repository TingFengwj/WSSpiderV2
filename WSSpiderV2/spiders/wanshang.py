# -*- coding: utf-8 -*-
import time, json, scrapy, socket, os, threading, traceback
from scrapy_redis.spiders import RedisSpider
from fake_useragent import UserAgent
from WSSpiderV2.spiders.basis import GeneralParse
from WSSpiderV2.utils.common import bytes_to_str, logger
from WSSpiderV2.settings import HTTP_HEADER, MAX_PROCESSES, client


def alive():
    try:
        myname = socket.getfqdn(socket.gethostname())
        my_ip = socket.gethostbyname(myname)
    except:
        logger.error(traceback.format_exc())
        my_ip = 'localhost'
    while True:
        # 本机IP + 进程ID 命名
        client.setex('spider_server:{0}_{1}'.format(my_ip, os.getpid()), '1', 70)
        time.sleep(60)


th = threading.Thread(target=alive)
th.setDaemon(True)
th.start()


class WanshangSpider(RedisSpider):
    name = 'wanshang'
    last_time = None

    # 队列中获取爬虫任务， 爬虫执行起点， 缓存任务来自..创建
    def next_requests(self):
        print('haha')
        if self.log_wait():
            print('>>轮询 redis 队列')
        use_set = self.settings.getbool('REDIS_START_URLS_AS_SET', False)
        print(use_set)
        fetch_one = self.server.spop if use_set else self.server.lpop
        found = 0
        self.redis_batch_size = MAX_PROCESSES  # 最大并行处理数
        while found < self.redis_batch_size:
            data = fetch_one(self.redis_key)
            if not data:
                break
            _spider_object = json.loads(bytes_to_str(data))
            _seed_url = _spider_object['base_url']
            print(_seed_url)
            headers = HTTP_HEADER
            headers['User-Agent'] = UserAgent().random
            if "cookie" in _spider_object["rules"].keys():
                headers['Cookie'] = _spider_object["rules"]['cookie']
            try:
                req = scrapy.Request(_seed_url, headers=headers, meta=_spider_object, dont_filter=True)
            except Exception as e:
                req = None
                logger.error('[Event: Request_Error, Result: failure, Message: base_url请求失败{},'
                             ' Error: {}, Data: (siteName_id:{}{})]'.format(e, req, _spider_object['siteName_id'],
                                                                            _spider_object['base_url']), exc_info=True)
            if req:
                yield req
                found += 1
            else:
                logger.error('[Event: Request_Error, Result: failure, Message: base_url请求失败,'
                             ' Error: {}, Data: (siteName_id:{}{})]'.format(str(req),
                                                                            str(_spider_object['siteName_id']),
                                                                            _spider_object['base_url']), exc_info=True)
        if found:
            logger.info('[Event: Read_Data, Result: success, Message: 获取爬虫配置数量{}, '
                        'Redis_Key: {}]'.format(found, self.redis_key), exc_info=True)

    # 解析来源
    def parse(self, response):
        """解析next_request方法返回的response，实例化爬虫为spider对象，调用process方法"""
        _class_config = response.meta
        print(_class_config)
        print(response)
        try:
            _spider = GeneralParse(_class_config)  # 爬虫实例化
            return _spider.process(response, self)
        except Exception as e:
            logger.error(
                '[Event: GeneralParse, Result: failure, Message: 实例化爬虫失败{}, Data: {}]'.format(e, str(_class_config)),
                exc_info=True)

    def parse_item(self, response):
        _parse = response.meta['parse']
        _method = getattr(_parse['obj'], _parse['method'])
        return _method(response, self)

    def log_wait(self, interval=3600):
        """判断此时项目是否达到时间间隔，以可以下次运行"""
        if self.last_time is None or time.time() - self.last_time > interval:
            self.last_time = time.time()
            return True
        return False
