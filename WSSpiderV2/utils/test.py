# -*- coding:utf-8 -*-

import jieba.analyse
import re


def get_keywords(con, weight=False):
    """
    :param con:需要提取关键词内容
    :param weight: 返回权重为True，不返回为False
    :return: 列表
    """
    con = ','.join(re.findall(r'[\u4e00-\u9fa5]+', con.strip()))
    jieba.load_userdict(r'C:\Users\Administrator\Desktop\user_dict.txt')
    jieba.analyse.set_stop_words(r'C:\Users\Administrator\Desktop\stop_word.txt')
    if weight:
        return [[i[0], round(i[1], 2)] for i in jieba.analyse.tfidf(con, topK=5, withWeight=weight)]
    else:
        return jieba.analyse.tfidf(con, topK=5, withWeight=weight)
