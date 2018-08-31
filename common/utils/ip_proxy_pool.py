#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie
# IP代理池

import requests

from common.utils.common import getNowDate
from common.utils.mongodb import MongodbCursor

mongodb = MongodbCursor()
ip_con = mongodb.get_cursor('common', 'ip')


def getProxyIp():
    """
    json格式如下：
        {"error_code":0,"error_message":"","data":[{"ip":"123.158.8.238","port":10039}]}
    :return:
    """
    api_500 = 'http://api.http.niumoip.com/v1/http/ip/get?p_id=93&s_id=2' \
              '&u=DW4HZQ46UjtbYAAuUB5XaAgnAj5dZQsaBFNTV1VT&number=1&port=1&type=1' \
              '&map=1&pro=0&city=0&pb=1&mr=2&cs=1'
    api_test = 'http://api.http.niumoip.com/v1/http/ip/get?p_id=702&s_id=1' \
               '&u=DW4HZQ46UjtbYAAuUB5XaAgnAj5dZQsaBFNTV1VT&number=1&port=1&type=1' \
               '&map=1&pro=0&city=0&pb=1&mr=2&cs=1'
    response = requests.get(api_500)
    ip = response.json()['data'][0]
    ip['type'] = 'http'
    ip['create_date'] = getNowDate()
    ip_con.insert(ip)
    return ip
