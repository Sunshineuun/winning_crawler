# -*- coding: UTF-8 -*-
import os
import traceback

import cx_Oracle

from common.property import ORACLE_INFO
from common.utils import mlogger

logger = mlogger.mlog
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
os.environ['path'] = 'H:\instantclient-basic-windows.x64-11.2.0.4.0\instantclient_11_2'


class OralceCursor(object):
    def __init__(self):
        self.minnie_oracle = cx_Oracle.connect(ORACLE_INFO, encoding='utf-8')
        self.oracle_cursor = self.minnie_oracle.cursor()
        if self.fechall('SELECT 1 FROM dual')[0][0] != 1:
            raise Exception('Database connection failed')
        logger.info('The database connection was successful')

    def executeSQLParams(self, sql, params):
        try:
            count = self.oracle_cursor.execute(sql, params)
            self.minnie_oracle.commit()
            return count
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            self.minnie_oracle.rollback()
            return 0

    def executeSQL(self, sql):
        try:
            count = self.oracle_cursor.execute(sql)
            self.minnie_oracle.commit()
            return count
        except Exception as e:
            logger.error(e)
            self.minnie_oracle.rollback()
            return 0

    def fechall(self, sql, params=None):
        if params is None:
            self.oracle_cursor.execute(sql)
        else:
            self.oracle_cursor.execute(sql, params)
        data = self.oracle_cursor.fetchall()
        return data

    def insertSQL(self, sql):
        try:
            count = self.oracle_cursor.execute(sql)
            self.minnie_oracle.commit()
            return count
        except Exception as e:
            logger.error(e)
            self.minnie_oracle.rollback()
            return 0


if __name__ == '__main__':
    """
        任务调度
    """
    cursor = OralceCursor()
