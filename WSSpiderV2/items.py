# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Wsspiderv2Item(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    article_id = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    web_url = scrapy.Field()
    channel = scrapy.Field()
    siteName_id = scrapy.Field()
    siteName = scrapy.Field()
    base_url = scrapy.Field()
    ctime = scrapy.Field()
    get_time = scrapy.Field()
