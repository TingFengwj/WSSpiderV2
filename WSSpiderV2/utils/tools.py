import json
import logging
import pymysql
from WSSpiderV2.settings import DATABASES, REDIS_KEY, client
logger = logging.getLogger('spider')


class DataExchange(object):
    def __init__(self):
        self.database = DATABASES.get('database')
        self.user = DATABASES.get('user')
        self.password = DATABASES.get('password')
        self.host = DATABASES.get('host')

    def deal_mysql(self, content):
        """读取数据库spider表中数据为json，返回json数据并入redis队列"""
        db = pymysql.connect(self.host, self.user, self.password, self.database)
        cursor = db.cursor()
        cursor.execute(content)
        dict_result = cursor.fetchall()
        xpath_json = [
            {'base_url': i[0], 'allow_img': i[1], 'allow_video': i[2], 'url_type': i[3], 'list_type': i[4],
             'next_type': i[5], 'siteName': i[7], 'index_url': i[8], 'site_type': i[9], 'rules': json.loads(i[10]),
             'siteName_id': i[11]} for i in dict_result]
        return xpath_json

    @staticmethod
    def db_insert(content):
        for item in content:
            client.rpush(REDIS_KEY, json.dumps(item))
        logger.info('load spider_list : %d' % len(content))


if __name__ == '__main__':
    result = DataExchange()
    # print(result.deal_mysql("""SELECT * FROM spider_list WHERE status_flag=1""")[0])
#     print(result.query("""SELECT * FROM spider_list WHERE status_flag=1"""))
#     DataExchange.db_insert(DataExchange, result.deal_mysql("""SELECT * FROM spider_list WHERE status_flag=1"""))
