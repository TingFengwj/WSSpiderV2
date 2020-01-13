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
            self.second_xpath = config.get('rules')['second_xpath']
        except Exception as e:
            logger.info(e)
            self.second_xpath = None
        self.xpath_title = config.get('rules')['xpath_title']
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
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/"
                      "*;q=0.8,application/signed-exchange;v=b3",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                          "like Gecko) Chrome/77.0.3865.90 Safari/537.36",
        }
        if "headers" in list(self.config.get('rules').keys()):
            headers = self.config.get('rules')['headers']
        return scrapy.Request(url, meta=_meta, callback=spider.parse_item, dont_filter=True,
                              headers=headers)

    # JSON 参数请求
    def make_json_request(self, url, callback, spider, body):
        _meta = {'parse': {'obj': self, 'method': callback.__name__}}
        return scrapy.Request(url, method='POST', body=json.dumps(body), headers={'Content-Type': 'application/json'},
                              meta=_meta, callback=spider.parse_item, dont_filter=False)

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
        if self.list_type == 1:  # 直接对应内容页面，只需要填充title，time，content的xpath即可
            yield self.parse_item(response=response, spider=spider)
        elif self.list_type == 2:
            if "second_xpath_re" in list(self.config.get('rules').keys()):
                text = response.text
                result = list(set(re.findall(r'%s' % self.config['rules']['second_xpath'], text)))
            else:
                result = list(set(response.xpath(self.config['rules']['second_xpath']).extract()))
            print(response.url)
            print(response.status)
            print(result)
            print('this is second result')
            _link = self.second_more_url(response=response, spider=spider, result=result)
            print(_link)
            for i in _link:
                yield self.make_request(url=i, callback=self.parse_item, spider=spider)
            net_url = self.next_url(spider=spider, response=response)
            print('next_url')
            print(net_url)
            if net_url:
                self.list_type = 2
                yield self.make_request(url=net_url, callback=self.process, spider=spider)
        elif self.list_type == 3:
            """三层列表页"""
            if "third_xpath_re" in list(self.config.get('rules').keys()):
                text = response.text
                result = list(set(re.findall(r'%s' % self.config['rules']['third_xpath'], text)))
            else:
                result = response.xpath(self.config['rules']['third_xpath']).extract()
            print(response.status)
            print(result)
            _link = self.third_more_url(response=response, spider=spider, result=result)
            print(_link)
            self.list_type = 2
            for i in _link:
                yield self.make_request(url=i, callback=self.process, spider=spider)
            if "second_detail_xpath" in list(self.config.get('rules').keys()):
                net_url = self.next_url(spider=spider, response=response)
                print('next_url')
                print(net_url)
                if net_url:
                    self.list_type = 3
                    yield self.make_request(url=net_url, callback=self.process, spider=spider)
        elif self.list_type == 4:
            """四层列表页"""
            if "fourth_xpath_re" in list(self.config.get('rules').keys()):
                text = response.text.decode('utf-8')
                result = list(set(re.findall(r'%s' % self.config['rules']['fourth_xpath'], text)))
            else:
                result = list(set(response.xpath(self.config['rules']['fourth_xpath']).extract()))
            print(self.config['rules']['fourth_xpath'])
            print(result)
            _link = self.fourth_more_url(response=response, spider=spider, result=result)
            self.list_type = 3
            for i in _link:
                yield self.make_request(url=i, callback=self.process, spider=spider)
        else:
            _href_list = response.xpath(self.xpath_list_link).extract()
            _title_list = response.xpath(self.xpath_title).extract()

    def second_more_url(self, response, spider, result):
        """第二层更多url,返回结果对应第一层请求的url"""
        _href_list = []
        rule_dict = self.config.get('rules')
        if "second_more_type" in list(rule_dict.keys()):
            second_more_type = rule_dict['second_more_type']
            if second_more_type == 1:  # 替换
                for i in result:
                    _href_list.append(urljoin(response.url, i))
            elif second_more_type == 2:  # 需要拼接主域名的url
                for i in result:
                    if not i.startswith('http'):
                        final_url = urljoin(self.config.get('index_url'), i)
                        end_url = final_url[0:6] + final_url[6::].replace('//', '/')
                        if '\\' in repr(end_url):
                            end_url = repr(end_url).replace('\\', '/')
                        _href_list.append(end_url)
                    else:
                        if '\\' in repr(i):
                            i = repr(i).replace('\\', '/')
                        _href_list.append(i)
            elif second_more_type == 3:  #
                for i in result:
                    if i.startswith('.'):
                        final_url = self.config.get('index_url') + i[1::]
                        _href_list.append(final_url[0:7] + final_url[7::].replace('//', '/'))
                    else:
                        _href_list.append(i)
            elif second_more_type == 5:  # 需要进行re匹配的url
                result = [re.findall(r'(/[a-z][A-Z]*.*htm[l]*)', j)[0] for j in result if j not in ['', '#', '/']]
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(self.config.get('index_url') + i)
            else:
                _href_list = result  # 不需要进行任何处理的url
        else:
            _href_list = result
        return _href_list

    def third_more_url(self, response, spider, result):
        """第三层更多url,返回结果对应第二层请求的url"""
        rule_dict = self.config.get('rules')
        if "third_more_type" in list(rule_dict.keys()):
            third_more_type = rule_dict['third_more_type']
            _href_list = []
            if third_more_type == 1:  # xpath解析到的结果直接为目标页面的url
                for i in result:
                    _href_list.append(urljoin(response.url, i))
            elif third_more_type == 2:  # 解析到需要拼接的url
                for i in result:
                    if '#' not in i:
                        if not i.startswith('http'):
                            new_url = self.config.get('index_url') + i
                            end_url = new_url[0:6] + new_url[6::].replace('//', '/')
                            if '\\' in repr(end_url):
                                end_url = repr(end_url).replace('\\', '/')
                            _href_list.append(end_url)
                        else:
                            if '\\' in repr(i):
                                i = repr(i).replace('\\', '/')
                            _href_list.append(i)
            elif third_more_type == 3:  #
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(i)
            elif third_more_type == 4:
                result = [re.findall(r'.*href=\"(.*)\"', j)[0].strip() for j in result]
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(i)
            elif third_more_type == 5:
                result = [re.findall(r'(/[a-zA-Z].*html)', j)[0] for j in result if j not in ['', '/', './']]
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(self.config.get('index_url') + i)
            elif third_more_type == 6:
                result = [re.findall(r'(/[a-zA-Z].*[html]*)', j)[0] for j in result if j not in ['', '/', './']]
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(self.config.get('index_url') + i)
            return _href_list
        else:
            return result

    def fourth_more_url(self, response, spider, result):
        """第四层更多url,返回结果对应第三层请求的url"""
        rule_dict = self.config.get('rules')
        if "fourth_more_type" in list(rule_dict.keys()):
            fourth_more_type = rule_dict['fourth_more_type']
            _href_list = []
            if fourth_more_type == 1:  # xpath解析到的结果直接为目标页面的url
                for i in result:
                    _href_list.append(urljoin(response.url, i))
            elif fourth_more_type == 2:  # 解析到需要拼接的url
                for i in result:
                    if '#' not in i:
                        if not i.startswith('http'):
                            final_url = self.config.get('index_url') + i
                            _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                        else:
                            _href_list.append(i)
            elif fourth_more_type == 3:  #
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(i)
            elif fourth_more_type == 4:
                result = [re.findall(r'.*href=\"(.*)\"', j)[0].strip() for j in result]
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(i)
            elif fourth_more_type == 5:
                result = [re.findall(r'(/[a-z].*html)', j)[0] for j in result]
                for i in result:
                    if i.startswith('.'):
                        final_url = response.url + i[1::]
                        _href_list.append(final_url[0:6] + final_url[6::].replace('//', '/'))
                    else:
                        _href_list.append(self.config.get('index_url') + i)
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
                    return _next_page_url
        elif self.config.get('next_type') == 2:
            try:
                _next_page_url = response.xpath(self.config.get('rules')['next_page']).extract()[-1]
            except Exception as e:
                logger.debug(e)
                _next_page_url = response.xpath(self.config.get('rules')['next_page']).extract_first()
            if _next_page_url:
                if _next_page_url.startswith('http'):
                    return _next_page_url
                else:
                    _next_page_url = self.config.get('index_url') + _next_page_url
                    return _next_page_url[0:6] + _next_page_url[6::].replace('//', '/')
            else:
                return None
        elif self.config.get('next_type') == 3:
            """框架翻页"""
            _next_page_url = re.findall(r'.*(/.*[a-z]*[0-9]*h)tm', response.url)
            if _next_page_url:
                page = re.findall(r'_([0-9][0-9]*[0-9]*).[a-zA-Z]*h', _next_page_url[0])
                if page:
                    new_page = str(int(page[-1]) + 1)
                    _next_page_url = response.url.replace(_next_page_url[0],
                                                          _next_page_url[0].replace(page[0], new_page))
                else:
                    _next_page_url = response.url.replace(_next_page_url[0], _next_page_url[0].replace('.', '_2.'))
            elif 'page' in response.url:
                page = re.findall(r'/page/([0-9][0-9]*[0-9]*)', response.url)
                if page:
                    new_page = int(page[0]) + 1
                    _next_page_url = response.url.replace(_next_page_url[0], page[0].replace(page[0], new_page))
                else:
                    _next_page_url = None
            else:
                _next_page_url = response.url + self.config.get('rules')['next_page']
            # raise 1
            if requests.get(url=_next_page_url):
                return _next_page_url
            else:
                return None
        elif self.config.get('next_type') == 4:
            try:
                _next_page_url = response.xpath(self.config.get('rules')['next_page']).extract_first()
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
            self.page_index += 1

            if self.page_index > 100:
                return None
            else:
                resp = requests.get(url=_next_page_url)
                if resp.status_code == 200:
                    return _next_page_url
                else:
                    return None

        elif self.config.get('next_type') == 6:
            """re匹配"""
            text = response.text
            _next_page_url = re.findall(r'%s' % self.config['rules']['next_page'], text)
            if _next_page_url:
                return urljoin(response.url, _next_page_url[0])
            else:
                return None

        elif self.config.get('next_type') == 7:
            if 'tml' in response.url:
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
            else:
                try:
                    _next_page_url = response.xpath(self.config.get('rules')['next_page']).extract()[-1]
                except Exception as e:
                    logger.debug(e)
                    _next_page_url = response.xpath(self.config.get('rules')['next_page']).extract_first()
                if _next_page_url:
                    if _next_page_url.startswith('http'):
                        return _next_page_url
                    else:
                        _next_page_url = response.url + '/' + _next_page_url
                        return _next_page_url[0:6] + _next_page_url[6::].replace('//', '/')
                else:
                    return None
            if requests.get(url=_next_page_url):
                return _next_page_url
            else:
                return None
        elif self.config.get('next_type') == 8:
            self.page_index += 1
            next_url = urljoin(response.url, '?uid=325&pageNum={}'.format(self.page_index))
            if self.page_index < 100:
                return next_url
            else:
                return None
        elif self.config.get('next_type') == 9:
            self.page_index += 1
            next_url = urljoin(response.url, '?page={}'.format(self.page_index))
            if self.page_index < 100:
                return next_url
            else:
                return None
        elif self.config.get('next_type') == 10:
            _next_page_url = re.findall(r'.*(/.*[a-z]*h)tm', response.url)
            if _next_page_url:
                page = re.findall(r'[0-9][0-9]*[0-9]*', _next_page_url[0])
                if page:
                    new_page = str(int(page[0]) + 1)
                    _next_page_url = response.url.replace(_next_page_url[0],
                                                          _next_page_url[0].replace(page[0], new_page))
                else:
                    _next_page_url = response.url.replace(_next_page_url[0], _next_page_url[0].replace('.', '_2.'))
            else:
                _next_page_url = response.url + 'default_1.htm'
            if requests.get(url=_next_page_url):
                return _next_page_url
            else:
                return None
        elif self.config.get('next_type') == 11:
            self.page_index += 1
            next_page = self.config.get('rules')['next_page']
            next_url = next_page.format(self.page_index)
            if self.page_index <= self.config.get('rules')['max_page']:
                return next_url
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
        if 'content' not in self.item.keys() or self.item['content'] is None or filter_pun(self.item['content']) == '':
            logger.error('content为空:web_url:{},xpath:{},siteName_id:{}, base_url:{}'.format(response.url,
                                                                                            self.config.get('rules')[
                                                                                                'content'],
                                                                                            self.config['siteName_id'],
                                                                                            self.config['base_url']))
        if self.item['content'] and self.item['title']:
            try:
                yield Wsspiderv2Item(article_id=self.item['article_id'], title=self.item['title'],
                                     content=self.item['content'],
                                     siteName_id=self.config.get('siteName_id'), web_url=self.item['web_url'],
                                     base_url=self.config.get('base_url'), siteName=self.config.get('siteName'),
                                     channel=self.item['channel'], ctime=self.item['ctime'],
                                     get_time=self.item['get_time'])
            except Exception as e:
                logger.error(e)

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
