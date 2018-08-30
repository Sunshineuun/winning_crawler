#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie

import datetime
import time
import re
import random

from common.base_crawler import BaseCrawler
from common.utils.common import reg
from common.utils.oracle import OralceCursor

insert_sql = """
INSERT INTO KBMS_DFSX_KNOWLEDGE_UP (ID, PRODUCT_NAME, TRAD_NAME, SPEC, PERMIT_NO,
                                    PRODUCTION_UNIT, CLINICAL_STATE, TYPE, IS_ENABLE, IS_SUBMIT)
SELECT *
FROM (
  SELECT
    T2.ID                                                                                                ID,
    DECODE(T1.PRODUCT_NAME, '', ('_' || T2.PRODUCT_NAME), T2.PRODUCT_NAME, ('_' || T2.PRODUCT_NAME), NULL, ('_' || T2.PRODUCT_NAME),
           ('#_' || T1.PRODUCT_NAME))                                                                    PRODUCT_NAME,
--       T1.PRODUCT_NAME CFDA产品名称, T2.PRODUCT_NAME 药品列表产品名称,
    DECODE(T1.TRAD_NAME, '', ('_' || T2.TRAD_NAME), T2.TRAD_NAME, ('_' || T2.TRAD_NAME), NULL, ('_' || T2.TRAD_NAME),
           ('#_' || T1.TRAD_NAME))                                                                       TRAD_NAME,
--       T1.TRAD_NAME CFDA商品名称, T2.TRAD_NAME 药品列表商品名称,
    DECODE(T1.SPEC, '', ('_' || T2.SPEC), T2.SPEC, ('_' || T2.SPEC), NULL, ('_' || T2.SPEC), ('#_' || T1.SPEC))                SPEC,
--       T1.SPEC CFDA规格, T2.SPEC 药品列表规格,
    DECODE(T1.PERMIT_NO, '', ('_' || T2.PERMIT_NO), T2.PERMIT_NO, ('_' || T2.PERMIT_NO), NULL, ('_' || T2.PERMIT_NO),
           ('#_' || T1.PERMIT_NO))                                                                       PERMIT_NO,
--       T1.PERMIT_NO CFDA批准文号, T2.PERMIT_NO 药品列表批准文号,
    DECODE(T1.PRODUCTION_UNIT, '', ('_' || T2.PRODUCTION_UNIT), T2.PRODUCTION_UNIT, ('_' || T2.PRODUCTION_UNIT), NULL,
           ('_' || T2.PRODUCTION_UNIT), ('#_' ||
                                         T1.PRODUCTION_UNIT))                                            PRODUCTION_UNIT,
--       T1.PRODUCTION_UNIT CFDA生产单位, T2.PRODUCTION_UNIT 药品列表生产单位,
    CASE WHEN T2.CLINICAL_STATE = '注销' AND T1.ID IS NOT NULL
      THEN '#_正常'
    WHEN T1.ID IS NOT NULL
      THEN '_正常'
    ELSE '_注销' END                                                                                       CLINICAL_STATE,
    '1'                                                                                                  TYPE,
    '1'                                                                                                  IS_ENABLE,
    '0'
      IS_SUBMIT
  FROM (SELECT
            ID,
            REPLACE(PRODUCT_NAME, ' ', '')    PRODUCT_NAME,
            REPLACE(TRAD_NAME, ' ', '')       TRAD_NAME,
            REPLACE(SPEC, ' ', '')            SPEC,
            ZC_FORM,
            REPLACE(PERMIT_NO, ' ', '')       PERMIT_NO,
            REPLACE(PRODUCTION_UNIT, ' ', '') PRODUCTION_UNIT,
            CODE_REMARK,
            TYPE,
            CREATE_TIME
          FROM KBMS_DFSX_KNOWLEDGE_UP_BAK) T1
    RIGHT JOIN KBMS_DRUG_FROM_SX T2 ON T1.ID = T2.ID
  WHERE TYPE = '1')
WHERE PRODUCT_NAME LIKE '#%'
      OR TRAD_NAME LIKE '#%'
      OR SPEC LIKE '#%'
      OR PERMIT_NO LIKE '#%'
      OR PRODUCTION_UNIT LIKE '#%'
      OR CLINICAL_STATE LIKE '#%'

"""
update_sql = """
UPDATE KBMS_DFSX_KNOWLEDGE_UP SET IS_ENABLE = '5' WHERE IS_ENABLE = '1'
"""

ZC_EX = ['气体', '医用氧(气态分装)', '医用氧', '医用氧(气态)', '化学药品', '医用气体', '医用气体(气态氧)',
         '其他', '气态', '液态和气态', '非剂型', '气态 液态', '体外诊断试剂', '鼻用制剂', '液态气体',
         '非制剂,其他:氧', '液态', '氧(气态、液态)', '液体	', '气剂', '液态氧', '气体、液态',
         '医用氧(液态)', '有效成份', '液态空气', '吸入性气体', '氧', '医用氧气', '氧气', '医用氧(气态、液态)',
         '呼吸', '其他:医用氧(气态)', '有效部位', '制剂中间体', '放免药盒', '药用辅料', '原料', '辅料',
         '特殊药用辅料', '颗粒剂(制剂中间体)', '制剂中间体水包衣颗粒', '制剂用中间体', '特殊辅料', '放射性密封源',
         '制剂:密封源', '放射性密封籽源', '药用辅料(供注射用)', '药用特殊辅料', '非制剂:辅料', '原料呀', '新辅料'
         ]
PRODUCT_NAME_EX = ['氧', '氧(液态)', '氧(气态)', '医用液态氧', '医用氧气', '医用氧(液态)']

RE_COMPILE = re.compile('869[0-9]{11}')


class cfda(BaseCrawler):
    """
    国家食品药品监督管理总局
    2018-3-27
        1.请求错误的url进行标记，因为发现有部分数据请求为空

    需要提交
    """

    def __init__(self):
        self.__domain_url = 'http://app1.sfda.gov.cn/datasearch/face3/'
        self.__href_re = 'javascript:commitForECMA[\u4e00-\u9fa50-9a-zA-Z\(\)\?&=,\'.]+'

        self.oralce_cursor = OralceCursor()
        super().__init__()

    def _get_cn_name(self):
        return 'CFDA'

    def _get_name(self):
        return 'cfda'

    def _init_url(self):
        """
        http://app1.sfda.gov.cn/datasearch/face3/search.jsp?tableId={code}&curstart={page}
        code:25代表国产药品，36代表进口药品
        page:翻页参数
        :return:
        """
        if self._urlpool.find_all_count():
            return

        url = 'http://app1.sfda.gov.cn/datasearch/face3/search.jsp?tableId={code}&curstart={page}'
        result = []
        p = {
            '国产': {
                'code': 25,
                'page': 11061
            },
            '进口': {
                'code': 36,
                'page': 274
            }
        }
        for k, v in p.items():
            for i in range(1, v['page'] + 1):
                p1 = {
                    'url': url.format(code=v['code'], page=i),
                    'type': 'CFDA-' + k,
                    'tree': 0
                }
                result.append(p1)
        return result

    def request(self, d):
        time.sleep(2)
        # home_url = 'http://app1.sfda.gov.cn/datasearch/face3/base.jsp?tableId=36&tableName=TABLE36&title=%BD%F8%BF%DA%D2%A9%C6%B7&bcId=124356651564146415214424405468'
        d1 = datetime.datetime.now()
        # self._crawler.driver_get_url(home_url)
        html = self._crawler.driver_get_url(d['url'])
        soup = self.to_soup(html)

        if d['tree'] == 0:
            a_tags = soup.find_all('a', href=re.compile(self.__href_re))

            if a_tags and len(a_tags):

                url_list = []
                # 更新链接请求成功
                for a in a_tags:
                    url_list.append({
                        'type': d['type'],
                        'url': self.__domain_url + reg(
                            'content.jsp\?tableId=[0-9]+&tableName=TABLE[0-9]+&tableView=[\u4e00-\u9fa50]+&Id=[0-9]+',
                            a['href']),
                        'text': a.text,
                        'tree': 1
                    })
                self._urlpool.save_url(url_list)
            else:
                return False, ''
        elif d['tree'] == 1:
            tbody = soup.find_all('tbody')
            if not tbody:
                time.sleep(random.randint(100, 300))
                self._crawler.update_proxy()
                return False, ''

        d2 = datetime.datetime.now()
        date = (d2 - d1).total_seconds()
        # 说明响应变慢了，等等，给服务器减压。
        # 存在请求小于0.1秒的情况，这些都是有数据，只是返回不正常
        # if date > 10 or date < 0.3:
        #     time.sleep(random.randint(100, 500))
        #     self._crawler.update_proxy()
        #     return False, ''

        return True, html

    def parser(self, d):
        soup = self.to_soup(d['html'])
        tr_tags = soup.find_all('tr')[1:-3]
        row = {
            '_id': d['_id'],
            'url': d['url'],
            'text': d['text']
        }
        for tr in tr_tags:
            text = tr.text.split('\n')
            if len(text) < 3:
                continue
            row[text[1]] = text[2]

        if '药品本位码' in row:
            text_b = RE_COMPILE.findall(d['text'])
            row_b = RE_COMPILE.findall(row['药品本位码'])
            text_b.sort()
            row_b.sort()

            # 数据有效加入，数据无效进行更新
            if ''.join(row_b).__contains__(''.join(text_b)):
                self._data_cursor.insert(row)
                return True
            else:
                return False
        else:
            return False

    def parser_target_condition(self):
        return {'tree': 1}

    def parser2(self):
        """
        比较原始数据列表上的本位码，是不是跟解析后的本位码一样
        1. 按照URL查取data，url中查找对应的数据
        2. 进行比较
        3. 不相同，那么删除html，更新url.isenable == 1
        :return:
        """
        index = 0
        for data in self._data_cursor().find():
            index += 1
            if index < 0:
                continue
            if index % 1000 == 0:
                print(index)
            if 'text' not in data:
                continue

            if ('药品本位码' not in data) or \
                    (data and not str(data['text']).__contains__(data['药品本位码'])):
                self._urlpool.update({'_id': data['_id']}, {'isenable': '1'})
                self._html_cursor.delete_one({'url': data['url']})

    def to_oracle(self):
        """
        数据转移到oracle上
        :return:
        """
        self.log.info('数据库存储开始')

        sql = 'INSERT INTO KBMS_DFSX_KNOWLEDGE_UP_BAK (ID, PRODUCT_NAME, TRAD_NAME, SPEC, ZC_FORM, PERMIT_NO, PRODUCTION_UNIT, CODE_REMARK, TYPE) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)'
        params = {
            'ID': ['药品本位码'],
            'PRODUCT_NAME': ['产品名称', '产品名称（中文）'],
            'TRAD_NAME': ['商品名', '商品名（中文）'],
            'SPEC': ['规格', '规格（中文）'],
            'ZC_FORM': ['剂型', '剂型（中文）'],
            'PERMIT_NO': ['批准文号', '注册证号'],
            'PRODUCTION_UNIT': ['生产单位', '生产厂商（英文）'],
            'CODE': ['药品本位码备注']
        }
        params1 = ['ID', 'PRODUCT_NAME', 'TRAD_NAME', 'SPEC', 'ZC_FORM', 'PERMIT_NO',
                   'PRODUCTION_UNIT', 'CODE']

        # 循环记录
        rows = []
        for i, data in enumerate(self._data_cursor.find()):
            if i % 10000 == 0 and i:
                self.oralce_cursor.executeSQLParams(sql, rows)
                rows.clear()
                self.log.info(i)
            row = ['0', '1', '2', '3', '4', '5', '6', '', '8']
            # 字典
            for i, k in enumerate(params1):
                # 字典中的数组
                for v in params[k]:
                    if v in data:
                        row[i] = data[v]

            # 剂型不在被收集队列里面；剂型不在排除队列里面；
            # 剂型不包含原料药，试剂这两个字样；剂型需要包含中文；
            # 剂型不为空；
            # 产品名称不在排除队列中；产品名称不包含试剂；
            if row[4] not in ZC_EX \
                    and not reg('(原料药)|(试剂)', row[4]) \
                    and reg('[\u4e00-\u9fa5]+', row[4]) \
                    and row[1] not in PRODUCT_NAME_EX \
                    and not reg('(试剂)', row[1]) \
                    and row[4]:
                """"""
                row[8] = '1'
            else:
                row[8] = '0'

            # 校验本位码农是否多个
            if len(row[0]) < 10:
                continue
            if row[7] != '':
                for code in row[7].split('；'):
                    row[0] = reg('[0-9]{14}', code)
                    row[3] = reg('\[.*\]', code).replace('[', '').replace(']', '')
                    rows.append(row)
            else:
                rows.append(row)

        # 更新数据
        # self.oralce_cursor.executeSQL(update_sql)
        # 插入数据
        # self.oralce_cursor.executeSQL(insert_sql)
        self.log.info('数据库存储结束')

    def htmlToOracle(self):
        cursor = OralceCursor(oracle_info='bian/bian@192.168.16.103/orcl')
        result = cursor.fechall("SELECT COUNT(1) FROM USER_TABLES WHERE TABLE_NAME = "
                                "'CFDA_HTML_HISTORY'")
        # 如果表不存在创建表
        if not result[0][0]:
            create_sql = """
            CREATE TABLE CFDA_HTML_HISTORY(
              ID VARCHAR(36),
              SOURCE VARCHAR(36),
              TYPE VARCHAR(36),
              URL VARCHAR(255),
              TREE VARCHAR(2),
              IS_ENABLE VARCHAR(2),
              HTML        CLOB,
              CREATE_DATE DATE
            )
            """
            cursor.executeSQL(create_sql)
        insert_sql = """
        INSERT INTO CFDA_HTML_HISTORY (ID, SOURCE, TYPE, URL, TREE, IS_ENABLE, HTML, CREATE_DATE)
              VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
        """
        keys = ['_id', 'source', 'type', 'url', 'tree', 'isenable', 'html', 'create_date']
        rows = []
        for i1, d in enumerate(self._html_cursor.find()[65307:]):
            if i1 % 10000 == 0 and i1:
                cursor.executeSQLParams(insert_sql, rows)
                rows.clear()
                self.log.info(i1)
            row = ['0', '1', '2', '3', '4', '5', '6', '7']
            for i, k in enumerate(keys):
                if k == 'create_date':
                    if not(type(d[k]) == datetime.datetime):
                        row[i] = datetime.datetime.strptime(d[k], '%Y-%m-%d %H:%M:%S')
                    else:
                        row[i] = d[k]
                    continue
                row[i] = str(d[k])
            rows.append(row)
        insert_sql = """
        INSERT INTO DATA_GATHER_COUNT (CODE, COUNT, TIME)
        select 'X008' CODE, COUNT(1) COUNT, TRUNC(MIN(CREATE_DATE), 'IW') TIME  from
          CFDA_HTML_HISTORY
        GROUP BY TO_CHAR(CREATE_DATE,'yyyy-IW')
        ORDER BY TO_CHAR(CREATE_DATE,'yyyy-IW')
        """
        cursor.executeSQL(insert_sql)


if __name__ == '__main__':
    cfda().htmlToOracle()
