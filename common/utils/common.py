#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie
import datetime

import re


def str_2_byte(s):
    """
    str to byte
    :param s:
    :return:
    """
    # sb2 = str.encode(s)
    bytes(s, encoding="utf8")


def byte_2_str(b):
    """
    byte to str
    :param b:
    :return:
    """
    # bytes.decode(b)
    str(b, encoding="utf8")


def encode(s):
    """
    转码
    :param s:
    :return:
    """
    return ' '.join([bin(ord(c)).replace('0b', '') for c in s])


def decode(s):
    """
    解码
    :param s:
    :return:
    """
    return ''.join([chr(i) for i in [int(b, 2) for b in s.split(' ')]])


def reg(pattern, s):
    """
    [\u4e00-\u9fa5]+ - 匹配中文
    :param pattern: 正则表达式
    :param s: 匹配对象
    :return: 匹配的第一条数据
    """
    # re.search(re.compile(pattern), s).group(0)
    ma = re.search(re.compile(pattern), s)
    if ma is not None:
        return ma.group(0)
    return ''


def getNowDate():
    # .strftime("%Y-%m-%d %H:%M:%S")
    return datetime.datetime.now()


def remove_blank(s):
    """
    删除s中的特殊字符（ \n\r）
    :param s:
    :return:
    """
    return re.sub('[  \n\r]', '', s)
