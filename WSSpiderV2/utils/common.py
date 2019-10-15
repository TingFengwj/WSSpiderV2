# -*- coding: utf-8 -*-
import datetime, time, re, json
import random
from os.path import dirname, realpath
from .bloom_filter import BloomFilter
import six
from WSSpiderV2.settings import REDIS_SPIDER_ERROR_LIST_KEY, client, LOGGING
import logging.config
import logging

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('spider')

BF = BloomFilter()
b_str = [str(x) for x in range(10)] + [chr(x) for x in range(ord('A'), ord('A') + 26)] + [chr(x) for x in
                                                                                          range(ord('a'),
                                                                                                ord('a') + 26)]


def filter_pun(string):
    r = r"[\s+\.\!\n\t\r\/_,$%^*(+\"\')]+|[+——()?【】《》“”‘’;；＂！，。·？、:：～~@#￥%……&*（）]+"
    return re.sub(r, '', string)


# 根据时间戳生成id  32进制
def get_rnd_id():
    ms = datetime.datetime.now().microsecond
    string_num = str(time.time())
    idx = string_num.find('.')
    string_num = '%s%s' % (string_num[0:idx], ms)
    num = int(string_num)
    mid = []
    while True:
        if num == 0: break
        num, rem = divmod(num, 62)
        mid.append(b_str[rem])
    return ''.join([str(x) for x in mid[::-1]])+random.choice(b_str)


# 当前时间
def get_now(format='%Y-%m-%d %H:%M:%S'):
    return time.strftime(format, time.localtime(time.time()))


def extract_date(string):
    """提取各种格式的日期时间"""
    string = string.strip()
    string = string.replace("十二月", "12").replace("十一月", "11").replace("十月", "10").replace("九月", "09").replace("八月",
                                                                                                              "08")
    string = string.replace("七月", "07").replace("六月", "06").replace("五月", "05").replace("四月", "04").replace("三月", "03")
    string = string.replace("二月", "02").replace("一月", "01")
    pattern = r'(\d{4})-(\d{1,2})-(\d{1,2} \d{1,2}:\d{1,2}:\d{1,2})'
    r = re.search(pattern, string)
    if r is not None:
        return r.group()
    pattern = r'(\d{4})-(\d{1,2})-(\d{1,2} \d{1,2}:\d{1,2})'
    r = re.search(pattern, string)
    if r is not None:
        return '{0}{1}'.format(r.group(), ':00')
    pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})'
    r = re.search(pattern, string)
    if r is not None:
        return '{0} {1}'.format(r.group(), '09:00:00')
    pattern = r'(\d{2})-(\d{1,2})-(\d{1,2})'
    r = re.search(pattern, string)
    if r is not None:
        return '{0} {1}'.format(r.group(), '09:00:00')

    pattern = r'(\d{4})/(\d{1,2})/(\d{1,2} \d{1,2}:\d{1,2}:\d{1,2})'
    r = re.search(pattern, string)
    if r is not None:
        return r.group().replace('/', '-')
    pattern = r'(\d{4})/(\d{1,2})/(\d{1,2} \d{1,2}:\d{1,2})'
    r = re.search(pattern, string)
    if r is not None:
        return '{0}{1}'.format(r.group().replace('/', '-'), ':00')
    pattern = r'(\d{4})/(\d{1,2})/(\d{1,2})'
    r = re.search(pattern, string)
    if r is not None:
        return '{0} {1}'.format(r.group().replace('/', '-'), '09:00:00')

    pattern = r'(\d{4})\.(\d{1,2})\.(\d{1,2} \d{1,2}:\d{1,2}:\d{1,2})'
    r = re.search(pattern, string)
    if r is not None:
        return r.group().replace('.', '-')
    pattern = r'(\d{4})\.(\d{1,2})\.(\d{1,2} \d{1,2}:\d{1,2})'
    r = re.search(pattern, string)
    if r is not None:
        return '{0}{1}'.format(r.group().replace('.', '-'), ':00')
    pattern = r'(\d{4})\.(\d{1,2})\.(\d{1,2})'
    r = re.search(pattern, string)
    if r is not None:
        return '{0} {1}'.format(r.group().replace('.', '-'), '09:00:00')
    
    pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
    r = re.search(pattern, string)
    if r is not None:
        return '{0} {1}'.format(string[6:] + '-' + string[3:5] + '-' + string[:2], '09:00:00')
    pattern = r'(\d{4})(\d{2})(\d{2})'
    r = re.search(pattern, string)
    if r is not None:
        return '{0} {1}'.format(string[:4] + '-' + string[4:6] + '-' + string[6:], '09:00:00')
    pattern = r'(\d{2}) (\d{1,2}), (\d{4})'
    r = re.search(pattern, string)
    if r is not None:
        if len(r.group(2)) == 1:
            return '{0} {1}'.format(r.group(3) + '-' + r.group(1) + '-0' + r.group(2), '09:00:00')
        elif len(r.group(2)) == 2:
            return '{0} {1}'.format(r.group(3) + '-' + r.group(1) + '-' + r.group(2), '09:00:00')
    pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日 \d{1,2}:\d{1,2}:\d{1,2}'
    r = re.search(pattern, string)
    if r is not None:
        return '{0} {1}'.format(r.group().replace('年', '-').replace('月', '-').replace('日', ''), '')

    pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日\d{1,2}:\d{1,2}'
    r = re.search(pattern, string)
    if r is not None:
        return '{0}{1}'.format(r.group().replace('年', '-').replace('月', '-').replace('日', ' '), ':00')

    pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日 \d{1,2}:\d{1,2}'
    r = re.search(pattern, string)
    if r is not None:
        return '{0}{1}'.format(r.group().replace('年', '-').replace('月', '-').replace('日', ' '), ':00')

    pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
    r = re.search(pattern, string)
    if r is not None:
        return '{0} {1}'.format(r.group().replace('年', '-').replace('月', '-').replace('日', ''), '09:00:00')

    pattern = r'(\d{1,2})分钟前'
    r = re.search(pattern, string)
    if r is not None:
        m = r.group(1)
        now = datetime.datetime.now()
        dt = datetime.timedelta(minutes=int(m))
        it_date = now - dt
        return it_date.strftime('%Y-%m-%d %H:%M:%S')
    pattern = r'(\d{1,2})小时前'
    r = re.search(pattern, string)
    if r is not None:
        m = r.group(1)
        now = datetime.datetime.now()
        dt = datetime.timedelta(hours=int(m))
        it_date = now - dt
        return it_date.strftime('%Y-%m-%d %H:%M:%S')
    pattern = r'(\d{1,2})天前'
    r = re.search(pattern, string)
    if r is not None:
        m = r.group(1)
        now = datetime.datetime.now()
        dt = datetime.timedelta(days=int(m))
        it_date = now - dt
        return it_date.strftime('%Y-%m-%d %H:%M:%S')

    pattern = r'(\d{1,2})-(\d{1,2} \d{1,2}:\d{1,2}:\d{1,2})'
    r = re.search(pattern, string)
    if r is not None:
        return '{0}-{1}'.format(datetime.datetime.now().strftime('%Y'), r.group())


def get_config(name):
    path = dirname(dirname(realpath(__file__))) + '/configs/' + name + '.json'
    with open(path, 'r', encoding='utf-8') as f:
        return json.loads(f.read())


def bytes_to_str(s, encoding='utf-8'):
    """Returns a str if a bytes object is given."""
    if six.PY3 and isinstance(s, bytes):
        return s.decode(encoding)
    return s


# 校验链接是否重复
def dupe_url_check(url):
    if url.endswith('/'):
        url = url[:-1]
    return BF.has_item(url) is False


def record_error(content):
    client.lpush(REDIS_SPIDER_ERROR_LIST_KEY, content)

