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
def readFile(file_name):
    """
    文件的全路径
    :param file_name:
    :return:
    """
    content = ''
    file_open = open(file_name, 'r', encoding='utf-8')  # r 代表read
    # for eachLine in file_open:
    #     content += eachLine
    content = file_open.read()
    file_open.close()
    return content


# 输入多行文字，写入指定文件并保存到指定文件夹
def writeFile(file_name, content):
    file_open = open(file_name, 'w')
    file_open.write('%s%s' % (content, os.linesep))
    file_open.close()

