# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from WSSpiderV2.items import Wsspiderv2Item
from WSSpiderV2.settings import LOGGING
from sqlalchemy import Column, String, Integer, Float, BigInteger, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from WSSpiderV2.settings import DATABASES
import logging.config
import logging

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('spider')


class Wsspiderv2Template():
    __tablename__ = 'article'
    web_url = Column(String, primary_key=True, unique=True)
    article_id = Column(String)
    title = Column(String)
    content = Column(String)
    channel = Column(String)
    siteName_id = Column(String)
    siteName = Column(String)
    base_url = Column(String)
    ctime = Column(String)
    get_time = Column(String)

    def __init__(self, **items):
        for key in items:
            if hasattr(self, key):
                setattr(self, key, items[key])


class Wsspiderv2Pipeline(object):
    def __init__(self):  # 执行爬虫时
        self.engine = create_engine('mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8mb4' % (
            DATABASES.get('user'), DATABASES.get('password'), DATABASES.get('host'), DATABASES.get('port'),
            DATABASES.get('database')), echo=True)
        # 连接数据库
        self.session = sessionmaker(bind=self.engine)
        self.sess = self.session()
        Base = declarative_base()
        # 动态创建orm类,必须继承Base, 这个表名是固定的,如果需要为每个爬虫创建一个表,请使用process_item中的
        self.Creative = type('wanshang', (Base, Wsspiderv2Template), {'__tablename__': 'article'})

    # def close_spider(self, spider):
    #     self.sess.close()
    #
    # def process_item(self, item, spider):
    #     self.sess.add(self.Creative(**item))
    #     try:
    #         self.sess.commit()
    #     except Exception as e:
    #         logger.info(e)
    #         self.sess.rollback()
    #
    #     return item

    def process_item(self, item, spider):
        # check if item with this title exists in DB
        item_exists = self.sess.query(self.Creative).filter_by(web_url=item['web_url']).first()
        # if item exists in DB - we just update 'date' and 'subs' columns.
        if item_exists:
            item_exists.title = item['title']
            item_exists.content = item['content']
            item_exists.ctime = item['ctime']
            print('Item {} updated.'.format(item['title']))
        # if not - we insert new item to DB
        else:
            new_item = self.Creative(**item)
            self.sess.add(new_item)
            print('New item {} added to DB.'.format(item['title']))
        try:
            self.sess.commit()
        except Exception as e:
            logger.info(e)
            self.sess.rollback()
        return item

    def close_spider(self, spider):
        # We commit and save all items to DB when spider finished scraping.
        self.sess.close()
