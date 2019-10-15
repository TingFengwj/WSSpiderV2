# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import json
import xlrd
import pymysql
import random
import datetime
import time

FilePath = r'C:\Users\zwjt\Desktop\inser_mysql(1)(1).xlsx'
b_str = [str(x) for x in range(10)] + [chr(x) for x in range(ord('A'), ord('A') + 26)] \
        + [chr(x) for x in range(ord('a'), ord('a') + 26)]


# 根据时间戳生成id  32进制
def get_rnd_id():
    ms = datetime.datetime.now().microsecond
    string_num = str(time.time())
    idx = string_num.find('.')
    string_num = '%s%s' % (string_num[0:idx], ms)
    num = int(string_num)
    mid = []
    while True:
        if num == 0:
            break
        num, rem = divmod(num, 62)
        mid.append(b_str[rem])
    return ''.join([str(x) for x in mid[::-1]])+random.choice(b_str)


def read_data_mysql(FilePath):
    """
    读取excel表中的数据☞mysql数据库中
    :param FilePath: Excel文件路径
    :return:
    """
    x1 = xlrd.open_workbook(FilePath)
    sheet1 = x1.sheet_by_index(0)
    col_len = len(sheet1.col_values(0))
    db = pymysql.connect('192.168.0.167', 'root', 'QWE@zw666', 'test_spiderv1')
    cursor = db.cursor()
    for j in range(1, col_len):
        row_value = sheet1.row_values(j)
        time.sleep(0.01)
        sql = """INSERT INTO `spider_list` VALUES ('%s', %d, %d, %d, %d, %d, %d, '%s', '%s', %d, '%s', '%s');""" % (
            str(row_value[0]), int(row_value[1]), int(row_value[2]), int(row_value[3]), int(row_value[4]),
            int(row_value[5]), int(row_value[6]), row_value[7], row_value[8], int(row_value[9]),
            pymysql.escape_string(json.dumps(json.loads(row_value[10].replace('\n', '')))), str(get_rnd_id()))
        # print(sql)
        try:
            cursor.execute(sql)
            db.commit()
        except Exception as e:
            print(e)
    cursor.close()
    db.close()
    return '数据已入库'


if __name__ == '__main__':
    # 注，Windows系统需要在filePath前加 ‘r’
    FilePath = r'C:\Users\zwjt\Desktop\inser_mysql(1)(1).xlsx'

    print(read_data_mysql(FilePath))
