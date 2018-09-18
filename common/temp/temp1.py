#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie

import json

import jieba
import pymongo

import datetime

from common.utils.common import remove_blank
from common.utils.excel import WriteXLSXCustom
from common.utils.mfile import getFilePaths, readFile, writeFile
from common.utils.mongodb import MongodbCursor
from common.property import MONGO_IP, MONGO_PORT
from common.utils.mlogger import mlog
from common.utils.oracle import OralceCursor

mongo = pymongo.MongoClient(MONGO_IP, MONGO_PORT)
log = mlog


def get_key(dbname):
    """
    获取mongodb表中，key的集合，因为mongodb中没条数据的key可能是不同的。
    :param dbname:
    :return:
    """
    cursor = mongo[dbname]['data']
    title = []
    for data in cursor.find():
        for k, v in data.items():
            if k not in title:
                title.append(k)
    print(title)
    return title


def count_url(name):
    """
    统计以抓取未抓取的url地址
    :param name:
    :param ip:
    :return:
    """
    html_cursor = mongo[name]['html']
    url_cursor = mongo[name]['url']
    data_cursor = mongo[name]['data']
    bak_cursor = mongo[name]['htmlbak']

    # for d in url_cursor.find():
    #     if type(d['insert_date']) == str:
    #         continue
    #     else:
    #         url_cursor.delete_one(d)
    #
    # for d in html_cursor.find():
    #     if type(d['insert_date']) == str:
    #         continue
    #     else:
    #         html_cursor.delete_one(d)

    # url = 'http://app1.sfda.gov.cn/datasearch/face3/search.jsp?tableId=25&curstart='
    # for d in range(3122, 6239):
    #     url_cursor.update({'url': url + str(d)}, {'$set': {'isenable': '0'}})
    #     html_cursor.delete_one({'url': url + str(d)})

    print('bakhtml-总数:', bak_cursor.find().count())
    print('html-总数:', html_cursor.find().count())
    print('url-总数:', url_cursor.find().count())
    print('url-未抓取:', url_cursor.find({'isenable': '1'}).count())
    print('url-已抓取:', url_cursor.find({'isenable': '0'}).count())
    print('data-解析的数量', data_cursor.find().count())

    # old = 0
    # for d in url_cursor.find({'isenable': '1'}):
    #     new = int(str(d['text']).split('.')[0])
    #     if old + 1 == new:
    #         old = new
    #         continue
    #     print(old, new)
    #     old = new
    #     print(d)
    #     print('____________________________')


def yaozh_monitored_count():
    """
    统计每个月的数量
    :return:
    """
    cursur = mongo['yaozh_monitored']['data']
    end = datetime.datetime.now()
    year = 2015
    month = 8
    while True:
        month += 1
        if month > 12:
            month = 1
            year += 1
        start = datetime.datetime(year, month, 1)
        print(
            start.strftime('%Y-%m'),
            cursur.find({'日期': {'$regex': start.strftime('%Y-%m')}}).count()
        )
        if start > end:
            break


def yaozh_unlabeleduse_update():
    cursor = mongo['yaozh_unlabeleduse']['url']
    print(
        cursor.remove({'url_': {'$exists': 'true'}})
    )
    print(
        cursor.update({'isenable': '0'}, {'$set': {'isenable': '1'}}, multi=True)
    )


def get_disease_info_utils(dis, disease_names):
    """
    :param dis:
    :param disease_names: 查询值得集合
    :return: 没有查询的值
    """
    datas = []
    excule_names = []
    cursor = mongo[dis['dbname']]['data']
    for d in cursor.find({dis['field']: {'$in': disease_names}}):
        excule_names.append(d[dis['field']])
        d['regex'] = d[dis['field']]
        d['key'] = d[dis['field']]
        datas.append(d)
    dis['datas'] = datas
    return list(set(disease_names).difference(set(excule_names)))


def find_name_by_disease_lib(name, disease_lib):
    lib = {
        'cnki_disease_lczl': {'dbname': 'cnki_disease_lczl', 'field': 'name'},
        'medlive_disease': {'dbname': 'medlive_disease', 'field': 'name'},
        '中国知网_医学知识库_疾病': {'dbname': '中国知网_医学知识库_疾病', 'field': '【 疾病名称 】'},
        'rw_disease': {'dbname': 'rw_disease', 'field': 'title'},
        'wiki8_disease': {'dbname': 'wiki8_disease', 'field': 'name'},
    }
    datas = []
    result = False
    ns = list(jieba.cut(name, cut_all=False))
    # (糖尿|2型|病){3,}
    regex = '(' + '|'.join(ns) + '){' + str(len(ns) // 2 + 1) + ',}'
    for k, v in lib.items():
        cursor = mongo[v['dbname']]['data']
        for d in cursor.find({v['field']: {'$regex': regex}}):
            result = True
            d['regex'] = regex
            d['key'] = name
            datas.append(d)
        disease_lib[k]['datas'] += datas
        datas.clear()
    return result


def getTitle():
    lib = {
        'cnki_disease_lczl': {'dbname': 'cnki_disease_lczl', 'field': 'name'},
        'medlive_disease': {'dbname': 'medlive_disease', 'field': 'name'},
        '中国知网_医学知识库_疾病': {'dbname': '中国知网_医学知识库_疾病', 'field': '【 疾病名称 】'},
        'rw_disease': {'dbname': 'rw_disease', 'field': 'title'},
        'wiki8_disease': {'dbname': 'wiki8_disease', 'field': 'name'},
    }
    for k, v in lib.items():
        title = []
        for data in mongo[k]['data'].find():
            for k, v in data.items():
                if k not in title and not str(k).__contains__('一篇') \
                        and not str(k).__contains__('阅读：'):
                    title.append(k)
        print(title)


def getHttpStatus(browser):
    """
    字典值：url,status,statusText
    :param browser:
    :return:
    """
    for responseReceived in browser.get_log('performance'):
        try:
            _json = json.loads(responseReceived[u'message'])
            # [u'message'][u'params'][u'response']
            if 'message' in _json \
                    and 'params' in _json['message'] \
                    and 'response' in _json['message']['params'] \
                    and 'requestHeaders' in _json['message']['params']['response'] \
                    and 'url' in _json['message']['params']['response'] \
                    and _json['message']['params']['response'][
                        'url'] == 'http://app1.sfda.gov.cn/4QbVtADbnLVIc/c.FxJzG50F.js?D9PVtGL=9a1adc':
                return _json['message']['params']['response']['requestHeaders']['Cookie']
        except BaseException as e:
            print(e)
            pass

    return False


def to_oracle():
    oralce_info = 'bian/bian@192.168.16.103/orcl'  # 数据库连接信息
    mongodb_dbname = 'cfda'  # mongodb数据库名称

    mongodb = MongodbCursor()
    oracle = OralceCursor(oralce_info)
    insert_sql = """
    INSERT INTO CFDA_DATA (ID, URL, TEXT, PZWH, OLD_PZWH, CPMC, EN_NAME, SPMC, JX, GG, SCDW,
    SCDZ, CPLB, PZRQ, CODE, CODE_NOTE) VALUES
      (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14, :15, :16)
    """
    keys = ['_id', 'url', 'text', '批准文号', '原批准文号', '产品名称', '英文名称', '商品名', '剂型', '规格', '生产单位',
            '生产地址', '产品类别', '批准日期', '药品本位码', '药品本位码备注']
    keys1 = ['_id', 'url', 'text', '注册证号', '原注册证号', '产品名称（中文）', '产品名称（英文）',
             '商品名（中文）', '剂型（中文）', '规格（中文）', '生产厂商（中文）',
             '厂商地址（中文）', '产品类别', '发证日期', '药品本位码', '药品本位码备注']

    result = oracle.fechall("SELECT COUNT(1) FROM USER_TABLES WHERE TABLE_NAME = 'CFDA_DATA'")
    # 如果表不存在创建表
    if not result[0][0]:
        create_sql = """
                CREATE TABLE CFDA_DATA(
                  ID VARCHAR(36),
                  URL VARCHAR(255),
                  TEXT VARCHAR(1000),
                  PZWH VARCHAR(255),
                  OLD_PZWH VARCHAR(255),
                  CPMC VARCHAR(255),
                  SPMC VARCHAR(255),
                  EN_NAME VARCHAR(255),
                  JX VARCHAR(255),
                  GG VARCHAR(1000),
                  SCDW VARCHAR(255),
                  SCDZ VARCHAR(255),
                  CPLB VARCHAR(255),
                  PZRQ VARCHAR(255),
                  CODE VARCHAR(255),
                  CODE_NOTE VARCHAR(1000)
                )
                """
        oracle.executeSQL(create_sql)

    rows = []
    for i1, d in enumerate(mongodb.get_cursor(mongodb_dbname, 'data').find()):
        if i1 % 10000 == 0 and i1:
            oracle.executeSQLParams(insert_sql, rows)
            rows.clear()
            print(datetime.datetime.now(), i1)

        row = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']
        try:
            for i, k in enumerate(keys):
                if k in d:
                    row[i] = str(d[k])
                else:
                    row[i] = str(d[keys1[i]])
            rows.append(row)
        except:
            print(1)
    oracle.executeSQLParams(insert_sql, rows)


def to_excel():
    mongo = MongodbCursor()
    cursor = mongo.get_cursor('pmmp_disease', 'data')
    titles = []
    write = WriteXLSXCustom('pmmp_disease.xlsx')
    for data in cursor.find():
        for k, v in data.items():
            if k not in titles:
                titles.append(k)

    rowindex = 0
    write.write(rowindex=rowindex, data=titles)

    for d in cursor.find():
        rowindex += 1
        row = []
        for k in titles:
            if k in d:
                row.append(remove_blank(str(d[k])))

        write.write(rowindex, row)
    write.close()


def update_mongodb():
    mongo = MongodbCursor()
    url_cur = mongo.get_cursor('pmmp_disease', 'url')
    data_cru = mongo.get_cursor('pmmp_disease', 'data')
    for d in url_cur.find({'isenable': '1'}):
        count = data_cru.find({'url': d['url']}).count()
        print(count)
        if count:
            url_cur.update({
                'url': d['url']
            }, {
                '$set': {
                    'isenable': '0'
                }
            }, multi=True)


def 转移文件():
    root = 'F:\邱胜明_资料\公司资料\\2018\\10_疾病资料爬取\DIS_IMAGE'
    path = 'F:\邱胜明_资料\公司资料\\2018\\10_疾病资料爬取\\KS\\{ks}\\{name}\\{image_name}'
    filelist = getFilePaths(root)
    for file in filelist:
        t = file.split('\\')[-3:]
        path1 = path.format(ks=t[1], name=t[0], image_name=t[2])
        writeFile(path1, readFile(file, mode='rb'), mode='wb')
    print(filelist)


if __name__ == '__main__':
    """
    """
    # 工具----------------------------------------------------------------------------------
    count_url('cfda_9')
    # count_url('药智网-药品中标信息')
    # common_to_excel()
    # A02()
    # get_disease_info()
    # mongo_test()
    # yaozh_monitored_count()
    # yaozh_unlabeleduse_update()
    # getTitle()
