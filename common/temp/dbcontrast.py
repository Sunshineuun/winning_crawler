#!/usr/bin/env python
# encoding=utf-8
import subprocess

import cx_Oracle
import os

import time

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
os.environ['path'] = 'H:\instantclient-basic-windows.x64-11.2.0.4.0\instantclient_11_2'


def fetchall(cursor, _sql):
    cursor.execute(_sql)
    return cursor.fetchall()


# kbms0705 = 'kbms/kbms675@192.168.16.167/orcl'
kbms0705 = 'kbms0705/kbms@192.168.16.113/sunshine'
kbms0812 = 'kbms0812/kbms@192.168.16.113/sunshine'

k7 = cx_Oracle.connect(kbms0705, encoding='utf-8')
k8 = cx_Oracle.connect(kbms0812, encoding='utf-8')

k7_cursor = k7.cursor()
k8_cursor = k8.cursor()

# 查询所有表
sql = 'SELECT T.TABLE_NAME FROM USER_TABLES T'
k7_cursor.execute(sql)

data = k7_cursor.fetchall()


def contrast():
    """
    1. 0705 不在 0812的 === 删除
    2. 0812 不在 0705的 === 新增
    3. 重复，但是变动过的 === 修改
    """
    for i, d in enumerate(data):
        time_start = time.time()
        # if i < 443:
        #     continue
        """
        大数据表
        KBMS_DRUG_STD_MAPPING_RESULT,KBMS_DRUG_SX_LIST_RTN,KBMS_MATERIAL_GJYJJ_2
        数据存在差异的表
        KBMS_DRUG_OLDPEOPLE,KBMS_DRUG_PREGNANT,KBMS_DRUG_REVERSE_MAPPING,KBMS_DRUG_SMALL_GENERIC
        KBMS_DRUG_SMALL_GENERIC_LFORM,KBMS_DRUG_TABOO,
        KBMS_EFFECT_REVERSE_KNOWLEDGE,KBMS_EFFECT_REVERSE_MAPPING,KBMS_KNOWLEDGE_REVIEW,KBMS_KNOWLEDGE_VERSION_INFO
        KBMS_KNOWLEDGE_VM,KBMS_LMIT_MEDICATIONS_DATA,KBMS_LMIT_MEDICATIONS_DATA_UP,KBMS_OUT_PRIMARY_CHINESE_DRUG
        KBMS_OUT_UNIQ_CHINESE_DRUG,KBMS_PROJECT_ENGINE_RELATION,KBMS_PROJECT_MAINTAIN,KBMS_ROLE_AUTHORITY
        KBMS_RULE_CHILD_MAPPING,KBMS_RULE_CHILD_MAPPING_STAGE,KBMS_RULE_CHILD_MEDICINE,KBMS_RULE_DIAGNOSIS
        无法导入的表
        CK02_ZLXM_WUXI_16_02_15 模拟
        """
        if d[0] in ['KBMS_KNOWLEDGE_FILE_MANAGE', 'KBMS_DRUG_MAPPING_ERROR',
                    'KBMS_MATERIAL_GJYJJ_2','CK02_ZLXM_WUXI_16_02_15',
                    'KBMS_TERM_OUT_PRIMARY_DRUG','KBMS_TERM_OUT_UNIQ_DRUG',
                    'KBMS_TERM_OUT_UNIQ_VFLC','KBMS_DRUG_MAPPING_ERROR','KBMS_VFLC_ITEM_MAPPING',
                    'KBMS_VFLC_ITEM_MAPPING_DETAIL','AAA','IL_INSTR_FILE_INFO',
                    'KBMS_CLINICAL_OPER_LOG','KBMS_DFSX_KNOWLEDGE_UP_BAK','KBMS_DRUG_DOSAGE_DT',
                    'KBMS_DRUG_EFFECT','KBMS_DRUG_EFFECT_COPY']:
            continue

        if not d[0] == 'KBMS_RULE_ITEM_REPETITION':
            continue
        # 查询是否有ID列
        _id = "SELECT * FROM user_tab_columns WHERE TABLE_NAME = '{}' AND COLUMN_NAME = 'ID'".format(
            d[0])
        id = fetchall(k7_cursor, _id)

        _sql = 'SELECT ID, T.* FROM {table} T'.format(table=d[0])
        if not id:
            _sql = 'SELECT T.* FROM {table} T'.format(table=d[0])

        print('{index}. {table}'.format(index=i, table=d[0]), end='')
        k7_d = fetchall(k7_cursor, _sql)
        k8_d = fetchall(k8_cursor, _sql)

        s = ' size : k7 is {s1}, k8 is {s2}'
        print(s.format(s1=len(k7_d), s2=len(k8_d)), end=' | ')

        if len(k7_d) == len(k8_d) and len(k7_d) > 500000:
            print('跳过')
            continue
        # k7 not in k8
        _k7 = {}
        __k7 = []
        for d1 in k7_d:
            # i += 1
            # if i % 5000 == 0:
            #     print(time.time() - time_start)
            #     time_start = time.time()
            if d1 not in k8_d:
                _k7[d1[0]] = d1
                __k7.append(d1)
            else:
                k8_d.remove(d1)  # 因为存在所以将其删除掉

        _k8 = {}
        for d1 in k8_d:
            # i += 1
            # if i % 5000 == 0:
            #     print(time.time() - time_start)
            #     time_start = time.time()

            if d1 not in __k7:
                _k8[d1[0]] = d1

        print('异常数据量：_k7-{k7}, _k8-{k8}'.format(k7=len(_k7), k8=len(_k8)), end=' | ')

        del_d = []
        for k, v in _k7.items():
            if k not in _k8:
                # 删除
                del_d.append(v)

        for v1 in del_d:
            _k7.pop(v1[0])

        add_d = []
        for k, v in _k8.items():
            if k not in _k7:
                # 删除
                add_d.append(v)

        for v1 in add_d:
            _k8.pop(v1[0])

        print('新增-{}, 删除-{}, _k8-{}, -k7-{}, 耗时-{}'.format(len(add_d), len(del_d), len(_k8),
                                                           len(_k7), '%.4f' % (time.time() -
                                                                               time_start)))


contrast()
