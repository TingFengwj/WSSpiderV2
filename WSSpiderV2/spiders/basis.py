# -*- coding: utf-8 -*-
from urllib.parse import urljoin

from fake_useragent import UserAgent
import scrapy
import re, json, datetime, time
from WSSpiderV2.settings import HTTP_HEADER, client
from WSSpiderV2.items import Wsspiderv2Item
from WSSpiderV2.utils.common import get_rnd_id, get_now, dupe_url_check, extract_date, filter_pun
from WSSpiderV2.settings import LOGGING
import requests
from scrapy.exceptions import DropItem
import logging.config
import logging

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('spider')


class BaseParse(object):
    last_url = None
    item = None

    def __init__(self, config):
        try:
            self.xpath_list_link = config.get('rules')['xpath_list_link']
        except Exception as e:
            logger.info(e)
            self.xpath_list_link = None
        self.xpath_list_title = config.get('rules')['xpath_list_title']
        self.list_type = config.get('list_type')
        self.config = config
        self.page_index = 1
        self.list_type2 = True
        self.last_url = self.get_last_url()
        self.stop = False

    def get_last_url(self):
        url = client.get('spider_pos_{0}'.format(self.config['siteName_id']))
        if url is not None:
            url = url.decode('utf-8')
        return url

    # 请求
    def make_request(self, url, callback, spider, params={}):
        _meta = dict(self.config, **params)
        _meta['parse'] = {'obj': self, 'method': callback.__name__}
        header = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/"
                      "*;q=0.8,application/signed-exchange;v=b3",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                          "like Gecko) Chrome/77.0.3865.90 Safari/537.36",
            "Referer": url}
        return scrapy.Request(url, meta=_meta, callback=spider.parse_item, dont_filter=True, headers=header)

    # JSON 参数请求
    def make_json_request(self, url, callback, spider, body):
        _meta = {'parse': {'obj': self, 'method': callback.__name__}}
        return scrapy.Request(url, method='POST', body=json.dumps(body), headers={'Content-Type': 'application/json'},
                              meta=_meta, callback=spider.parse_item)

    def _get_headers(self, referer, params={}):
        headers = dict(HTTP_HEADER, **params)
        headers['User-Agent'] = UserAgent().random
        if referer is not None or referer != '':
            headers['Referer'] = referer
        return headers


class GeneralParse(BaseParse):
    """处理列表"""

    def process(self, response, spider):
        """'此时根据列表类型不同，分别对各种类型的列表页进行处理'"""
        _href_list = []
        _title_list = []
        # 列表类型(1：进入为正文，2：带有子列表页，3: ajax请求，4：其它乱序的,)
        if self.list_type == 1:
            yield self.parse_item(response=response, spider=spider)
            net_url = self.next_url(spider=spider, response=response)
            if net_url:
                yield self.make_request(url=net_url, callback=self.process, spider=spider)
        elif self.list_type == 2:
            result = response.xpath(self.config['rules']['xpath']).extract()
            # print(response.text)
            print(response.url)
            print(result)
            print('this is result')
            _link = self.more_url(response=response, spider=spider, result=result)
            print(_link)
            for i in _link:
                yield self.make_request(url=i, callback=self.parse_item, spider=spider)
            net_url = self.next_url(spider=spider, response=response)
            print(net_url)
            if net_url:
                yield self.make_request(url=net_url, callback=self.process, spider=spider)
        elif self.list_type == 3:
            _data = response.body.decode('utf-8')
            _title_list = re.findall(eval(self.xpath_list_title), _data)
            _href_list = re.findall(eval(self.xpath_list_link), _data)
            if self.config['rules']['xpath_time_re']:
                _time_list = re.findall(eval(self.config['rules']['xpath_time_re']), _data)
        elif self.list_type == 4:
            pass
        elif self.list_type == 5:  # 三层列表页
            if "request_time" in list(response.meta.keys()):
                request_time = response.meta['request_time']
                if request_time == 1:
                    print(self.config['rules']['xpath_list_link'])
                    result = response.xpath(self.config['rules']['xpath_list_link']).extract()
                    print('解析主目录结果')
                    print(response.url)
                    print(result)
                    print('解析到结果为上')
                    _href_list = self.list_more_url(response=response, spider=spider, result=result)
                    print(_href_list)
                    if len(_href_list) > 0:
                        for index in range(len(_href_list)):
                            url = _href_list[index]
                            yield self.make_request(url, self.parse_item, spider)
                        net_url = self.next_url(spider=spider, response=response)
                        print('下一页url是')
                        print(response.url)
                        print(net_url)
                        if net_url:
                            yield self.make_request(url=net_url, callback=self.process, spider=spider,
                                                    params={"request_time": 1})
            else:
                print(response.url)
                print(self.config['rules']['xpath'])
                result = response.xpath(self.config['rules']['xpath']).extract()
                print('this is result')
                print(result)
                # raise 1
                _link = self.more_url(response=response, spider=spider, result=result)
                print(_link)
                print(len(_link))
                # raise 1
                for i in _link:
                    try:
                        yield self.make_request(url=i, callback=self.process, spider=spider, params={"request_time": 1})
                    except Exception as e:
                        logger.info(e)
        elif self.list_type == 6:  # 四层列表页
            if "request_time" in list(response.meta.keys()):
                request_time = response.meta['request_time']
                if request_time == 1:
                    text = response.text
                    # 创建一个 Selector 类的实例
                    print(self.config['rules']['xpath_list_link'])
                    result = list(set(re.findall(r'%s' % self.config['rules']['xpath_list_link'], text)))
                    print(result)
                    print('解析主目录结果')
                    print(response.url)
                    print(result)
                    print('解析到结果为上')
                    _href_list = self.list_more_url(response=response, spider=spider, result=result)
                    print(_href_list)
                    print(len(_href_list))
                    # raise 2
                    # print(_href_list)
                    if len(_href_list) > 0:
                        for index in range(len(_href_list)):
                            url = _href_list[index]
                            yield self.make_request(url, self.parse_item, spider)
                        net_url = self.next_url(spider=spider, response=response)
                        print('下一页url是')
                        print(response.url)
                        print(net_url)
                        if net_url:
                            yield self.make_request(url=net_url, callback=self.process, spider=spider,
                                                    params={"request_time": 1})
            else:
                if "first_re" in list(self.config.get('rules').keys()):
                    text = response.text
                    # 创建一个 Selector 类的实例
                    print(self.config['rules']['xpath_list_link'])
                    result = re.findall(r'%s' % self.config['rules']['xpath'], text)
                else:
                    print(self.config['rules']['xpath'])
                    result = list(set(response.xpath(self.config['rules']['xpath']).extract()))
                    print('this is result')
                    print(result)
                _link = self.more_url(response=response, spider=spider, result=result)
                print(response.url)
                print(_link)
                print(len(_link))
                for i in _link:
                    try:
                        yield self.make_request(url=i, callback=self.process, spider=spider, params={"request_time": 1})
                    except Exception as e:
                        logger.info(e)
        else:
            _href_list = response.xpath(self.xpath_list_link).extract()
            _title_list = response.xpath(self.xpath_list_title).extract()

    def list_more_url(self, response, spider, result):
        _href_list = []
        rule_dict = self.config.get('rules')
        if "list_more_url_type" in list(rule_dict.keys()):
            list_more_url_type = rule_dict['list_more_url_type']
            if list_more_url_type == 2:  # 需要拼接主域名的url
                for i in result:
                    if not i.startswith('http'):
                        _href_list.append(self.config.get('index') + i)
                    else:
                        _href_list.append(i)
            elif list_more_url_type == 5:  # 需要进行re匹配的url
                result = [re.findall(r'(/[a-z]*[A-Z]*.*html)', j)[0] for j in result]
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(self.config.get('index') + i)
            else:
                _href_list = result  # 不需要进行任何处理的url
        else:
            _href_list = result
        return _href_list

    def more_url(self, response, spider, result):
        rule_dict = self.config.get('rules')
        if "more_url_type" in list(rule_dict.keys()):
            more_url_type = rule_dict['more_url_type']
            _href_list = []
            if more_url_type == 1:  # xpath解析到的结果直接为目标页面的url
                return result
            elif more_url_type == 2:  # 解析到需要拼接的url
                for i in result:
                    if '#' not in i:
                        if not i.startswith('http'):
                            _href_list.append(self.config.get('index') + i)
                        else:
                            _href_list.append(i)
            elif more_url_type == 3:  #
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(i)
            elif more_url_type == 4:
                result = [re.findall(r'.*href=\"(.*)\"', j)[0].strip() for j in result]
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(i)
            elif more_url_type == 5:
                result = [re.findall(r'(/[a-z].*html)', j)[0] for j in result]
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(self.config.get('index') + i)
            return _href_list
        else:
            return result

    # 翻页
    def next_url(self, response, spider):
        if self.config.get('next_type') == 1:
            _next_page_url = response.xpath(self.config.get('rules')['next_page']).extract_first()
            if _next_page_url is not None and "javascript" not in _next_page_url and "#" != _next_page_url and _next_page_url != "":
                _next_page_url = urljoin(response.url, _next_page_url)
                if _next_page_url != response.url:
                    print('response--channel_type', _next_page_url, self.config.get('next_type'))
                    return _next_page_url
        elif self.config.get('next_type') == 2:
            _next_page_url = response.xpath(self.config.get('rules')['next_page']).extract_first()
            if _next_page_url:
                if _next_page_url.startswith('http'):
                    return _next_page_url
                else:
                    _next_page_url = self.config.get('index') + _next_page_url
                    return _next_page_url[0:6] + _next_page_url[6::].replace('//', '/')
            else:
                return None
        elif self.config.get('next_type') == 3:
            """框架翻页"""
            _next_page_url = re.findall(r'.*(/.*[a-z]*h)tml', response.url)
            if _next_page_url:
                page = re.findall(r'[0-9][0-9]*[0-9]*', _next_page_url[0])
                if page:
                    new_page = str(int(page[0]) + 1)
                    _next_page_url = response.url.replace(_next_page_url[0],
                                                          _next_page_url[0].replace(page[0], new_page))
                else:
                    _next_page_url = response.url.replace(_next_page_url[0], _next_page_url[0].replace('.', '_2.'))
            else:
                if 'page' in response.url:
                    page = re.findall(r'/page/([0-9][0-9]*[0-9]*)', response.url)
                    if page:
                        new_page = int(page[0]) + 1
                        _next_page_url = response.url.replace(_next_page_url[0], page[0].replace(page[0], new_page))
                    else:
                        _next_page_url = None
                else:
                    _next_page_url = response.url + '/page/2'
            if requests.get(url=_next_page_url):
                return _next_page_url
            else:
                return None
        elif self.config.get('next_type') == 4:
            try:
                print('找下一页xpath是')
                print(self.config.get('rules')['next_page'])
                _next_page_url = response.xpath(self.config.get('rules')['next_page']).extract_first()
                print(_next_page_url)
                if 'tml' in _next_page_url:
                    _next_page_url = "/".join(response.url.split('/')[0:-1]) + '/' + _next_page_url.split('\'')[1]
                else:
                    _next_page_url = response.url + '/' + _next_page_url
            except Exception as e:
                logger.info(e)
                _next_page_url = None
            return _next_page_url
        elif self.config.get('next_type') == 5:
            _next_page_url = urljoin(response.url, self.config.get('rules')['next_url'].format(self.page_index))
            # _next_page_url = self.config.get('rules')['next_url']
            # if response.url == self.config.get('rules')['next_url']:
            #     _next_page_url = response.url
            self.page_index += 1

            # page = re.findall(r'%s' % self.config.get('rules')['next_page'], _next_page_url)
            print(response.url)
            print(_next_page_url)
            print('this is next page')
            if self.page_index == 10:
                raise 1
            # if page:
            #     number = re.findall(r'([0-9][0-9]*[0-9]*)', page[0])
            #     next_number = str(int(number[0]) + 1)
            #     new_page = page[0].replace(number[0], next_number)
            #     _next_page_url = self.config.get('rules')['next_url'].replace(page[0], new_page)
            #     print(_next_page_url)
            # else:
            #     _next_page_url = ''
            resp = requests.get(url=_next_page_url)
            if resp.status_code == 200:
                return _next_page_url
            else:
                return None

        elif self.config.get('next_type') == 6:
            """re匹配"""
            text = response.text
            print(self.config['rules']['next_page'])
            _next_page_url = re.findall(r'%s' % self.config['rules']['next_page'], text)
            if _next_page_url:
                return _next_page_url[0]
            else:
                return None

    def parse_item(self, response, spider):
        self.item = {'get_time': get_now(), 'web_url': response.url, 'article_id': get_rnd_id()}
        try:
            _title = response.xpath(self.config.get('rules')['title']).extract()
        except Exception as e:
            logger.error('未解析到title: web_url:{},xpath:{},siteName_id:{}, base_url:{}'.format(response.url,
                                                                                             self.config.get('rules')[
                                                                                                 'title'],
                                                                                             self.config['siteName_id'],
                                                                                             self.config['base_url']))
            _title = response.meta.get('list_title')
        if _title is None and 'list_title' in response.meta.keys() or not _title:
            _title = response.meta.get('list_title')
        self.item['title'] = filter_title(_title)
        try:
            self.item['content'] = filter_content(
                ''.join(response.xpath(self.config.get('rules')['content']).extract()))
        except Exception as e:
            logger.error('未解析到content:web_url:{},xpath:{},siteName_id:{}, base_url:{}'.format(response.url,
                                                                                              self.config.get('rules')[
                                                                                                  'content'],
                                                                                              self.config[
                                                                                                  'siteName_id'],
                                                                                              self.config['base_url']))
        self.item['channel'] = self.config.get('url_type')
        if "datetime" in self.config.get('rules').keys():
            try:
                _publish_date = response.xpath(self.config.get('rules')['datetime']).extract_first()
                self.item['ctime'] = extract_date(filter_publish(_publish_date))  # 解析文章的发布时间
            except Exception as e:
                if 'list_time' in self.config.keys():
                    self.item['ctime'] = extract_date(self.config.get('list_time'))
                else:
                    self.item['ctime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 生成文章的发布时间
        else:
            self.item['ctime'] = get_now()
        if 'title' not in self.item.keys() or self.item['title'] is None or filter_pun(self.item['title']) == '':
            logger.error('title为空: web_url:{},xpath:{},siteName_id:{}, base_url:{}'.format(response.url,
                                                                                           self.config.get('rules')[
                                                                                               'title'],
                                                                                           self.config['siteName_id'],
                                                                                           self.config['base_url']))
            # raise DropItem(u"{0} 标题为空 {1}".format(self.item['article_id'], self.item['web_url']))
        if 'content' not in self.item.keys() or self.item['content'] is None or filter_pun(self.item['content']) == '':
            logger.error('content为空:web_url:{},xpath:{},siteName_id:{}, base_url:{}'.format(response.url,
                                                                                            self.config.get('rules')[
                                                                                                'content'],
                                                                                            self.config['siteName_id'],
                                                                                            self.config['base_url']))
            # raise DropItem(u"{0} 正文为空 {1}".format(self.item['article_id'], self.item['web_url']))
        print(self.item)
        # yield Wsspiderv2Item(article_id=self.item['article_id'], title=self.item['title'], content=self.item['content'],
        #                      siteName_id=self.config.get('siteName_id'), web_url=self.item['web_url'],
        #                      base_url=self.config.get('base_url'), siteName=self.config.get('siteName'),
        #                      channel=self.item['channel'], ctime=self.item['ctime'], get_time=self.item['get_time'])

    def fetch_image(self, matched):
        return urljoin(self.config['base_url'], matched.group(1))


def filter_content(content):
    """过滤正文, 处理和替换正文content中不正常的格式"""
    content = re.sub(r'<br.*?>', '', content)
    content = re.sub(r'<div.*?>', '<div>', content)
    content = re.sub(r'<section.*?>', '<section>', content)
    content = re.sub(r'<colgroup.*?>', '<colgroup>', content)
    content = re.sub(r'<p.*?>', '<p>', content)
    content = re.sub(r'<span.*?>', '<span>', content)
    content = re.sub(r'<strong.*?>', '<strong>', content)
    content = re.sub(r'<tbody.*?>', '<tbody>', content)
    content = re.sub(r'<table.*?>', '<table>', content)
    content = re.sub(r'<tr.*?>', '<tr>', content)
    # content = re.sub(r'<td.*?>', '<td>', content)
    content = re.sub(r'<label .*?>', '<label >', content)
    content = re.sub(r'<select .*?>', '<select >', content)
    content = re.sub(r'<embed.*?>', '<embed>', content)
    content = re.sub(r'<param.*?>', '<param>', content)
    content = re.sub(r'<ul.*?>', '<ul>', content)
    content = re.sub(r'<li.*?>', '<li>', content)
    content = re.sub(r'<h1.*?>', '<h1>', content)
    content = re.sub(r'<h2.*?>', '<h2>', content)
    content = re.sub(r'<h3.*?>', '<h3>', content)
    content = re.sub(r'<h4.*?>', '<h4>', content)
    content = re.sub(r'<h5.*?>', '<h5>', content)
    content = re.sub(r'<style.+?</style>', '', content, flags=re.S)
    content = re.sub(r'<script.+?</script>', '', content, flags=re.S)
    content = content.replace("\r", "").replace("\t", "").replace("\n", "")
    # content = re.sub('<img .*? src="([^""]*)".*?>', self.fetch_image, content)
    return content


def filter_title(title):
    """过滤标题"""
    if title is not None:
        title = re.sub('[\r|\n|\t|  |  ]', '', "".join(title))
    return title


def filter_publish(publish):
    """处理日期"""
    if publish is not None:
        publish = re.sub('发布日期：', '', publish.replace('\n', ''))
        publish = re.sub('发布时间:', '', publish)
        publish = re.sub('发表时间：', '', publish)
    return publish
