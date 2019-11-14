from scrapy import cmdline
from WSSpiderV2.settings import REDIS_CONFIG, client, REDIS_KEY
from WSSpiderV2.utils.tools import DataExchange
from WSSpiderV2.utils.common import get_config
import json


def run():
    # print(json.dumps(get_config("diagnostics")))
    client.rpush(REDIS_KEY, json.dumps(get_config("diagnostics")))      # 读json
    # result = DataExchange()
    # print(result.deal_mysql("""SELECT * FROM spider_list WHERE status_flag=1"""))
    # DataExchange.db_insert(result.deal_mysql("""SELECT * FROM spider_list WHERE status_flag=1"""))
    cmdline.execute('scrapy crawl wanshang'.split())


if __name__ == '__main__':
    run()
