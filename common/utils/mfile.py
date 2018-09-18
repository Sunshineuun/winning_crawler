#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie
import os


# 遍历指定目录，获取目录下的所有文件名
def getFilePaths(rootDir, fileName='', fileList=None):
    """
    获取rootDir\\fileName目录下在的文件
    :param rootDir: 根目录
    :param fileName: 文件名称或者目录名称
    :param fileList: 文件列表，原则上用户存储文件绝对路径的list
    :return: fileList
    """
    if fileList is None:
        fileList = []
    rootDir = os.path.join(rootDir, fileName)
    for each1 in os.listdir(rootDir):
        fileName1 = os.path.join(rootDir, each1)
        if os.path.isfile(fileName1):
            fileList.append(fileName1)
        elif os.path.isdir(fileName1):
            getFilePaths(rootDir, fileName1, fileList=fileList)
    return fileList


# 读取文件内容并打印
def readFile(file_name, encoding='utf-8', mode='r'):
    """
    文件的全路径
    :param mode:
    :param encoding:
    :param file_name:
    :return:
    """
    file_open = open(file_name, mode=mode)  # r 代表read
    content = file_open.read()
    file_open.close()
    return content


# 输入多行文字，写入指定文件并保存到指定文件夹
def writeFile(file_name, content, mode='w'):
    path1 = '\\'.join(file_name.split('\\')[:-1])
    if not os.path.exists(path1):
        os.makedirs(path1)
    file_open = open(file_name, mode=mode)
    file_open.write(content)
    file_open.close()
