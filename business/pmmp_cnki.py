#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie
# http://pmmp.cnki.net/Resources/CDDPdf/dis/base/%E8%82%BF%E7%98%A4%E7%A7%91/%E7%BA%B5%E9%9A%94%E5%9B%8A%E8%82%BF%E5%8F%8A%E8%82%BF%E7%98%A4.pdf
# 疾病
import os
import urllib

import requests
import time
from bs4 import BeautifulSoup
from bs4 import Tag
from selenium.webdriver.support.select import Select

from common.base_crawler import BaseCrawler
from common.exception.Exception import ValidationException
from common.utils.common import readFile, remove_blank
from common.utils.crawler import Crawler
from common.utils.mongodb import MongodbCursor


class disease(BaseCrawler):
    def __init__(self, is_porxy):
        self.key = []
        super().__init__(is_porxy=is_porxy)

    def _init_url(self):
        result = []
        url = 'http://pmmp.cnki.net/cdd/Disease/Dis_Basic.aspx'
        result.append({
            'url': url,
            'type': self._get_cn_name(),
            'tree': 0
        })
        return result

    def parser(self, d):
        pass

    def pushMail(self):
        pass

    def request(self, d):
        time.sleep(2)
        key = ['疾病名', '英文名', '别名', '疾病分类', 'ICD号']
        html = self._crawler.driver_get_url(d['url'])
        soup = self.to_soup(html)
        if (d['tree']) == 0:
            driver = self._crawler.driver
            # 获取并点击提交按钮
            submit = driver.find_element_by_id('DS_Basic1_btnSubmit')
            submit.click()
            # 改变每页显示的数量
            pageCount = Select(driver.find_element_by_id('DS_Basic1_DropNumber'))
            pageCount.select_by_index(2)

            soup = self.to_soup(driver.page_source)

            # 下一页按钮
            nextButton = driver.find_element_by_id('DS_Basic1_linkNext')
            nextButton1 = soup.find('a', id='DS_Basic1_linkNext')
            while 'disabled' not in nextButton1.attrs:
                # 获取当前页面数据
                soup = self.to_soup(driver.page_source)
                _trs = soup.find('table', id='DS_Basic1_listResult').find('table').find_all('tr')
                for _tr in _trs[1:]:
                    tds = _tr.find_all('td')
                    # 当tr中只有一个td的时候
                    if len(tds) == 1:
                        continue
                    row = {
                        'url': 'http://pmmp.cnki.net/cdd/Disease/' + tds[1].a['href'],
                        'tree': 1
                    }
                    for i, td in enumerate(tds[1:-1]):
                        span = td.find('span')
                        if 'title' in span.attrs:
                            text = span['title']
                        else:
                            text = span.text
                        row[key[i]] = text
                    self._urlpool.save_url(row)
                nextButton.click()
                nextButton = driver.find_element_by_id('DS_Basic1_linkNext')
                soup = self.to_soup(driver.page_source)
                nextButton1 = soup.find('a', id='DS_Basic1_linkNext')
            return True, ''
        elif (d['tree']) == 1:
            td = soup.find('td', class_='style8')
            trs = td.table.tbody.contents
            trs1 = []
            for tr in trs:
                if type(tr) == Tag:
                    trs1.append(tr)

            row = {}
            for i in range(0, trs1.__len__(), 2):
                text = remove_blank(trs1[i].text)[:-1]
                content = remove_blank(trs1[i + 1].text)
                if not content.startswith(text):
                    continue
                    # raise ValidationException('验证异常')
                if text not in self.key:
                    key.append(text)
                row[text] = content

                imgs = trs1[i + 1].find_all('img')
                for img in imgs:
                    src = 'http://pmmp.cnki.net/cdd/' + img['src'][3:]
                    filepath = 'D:/Temp/DIS_IMAGE1' + '/' + d['疾病分类'] + '/' + d['疾病名'] + '/'
                    if not os.path.exists(filepath):
                        os.makedirs(filepath)
                    filename = filepath + src.split('/')[-1]
                    r = requests.get(src)
                    with open(filename, "wb") as f:  # 开始写文件，wb代表写二进制文件
                        f.write(r.content)
            row.update(d)
            self._data_cursor.insert(row)
            return True, html

    def _get_name(self):
        return 'pmmp_disease'

    def _get_cn_name(self):
        return 'pmmp_疾病1'


def download_pdf():
    path = 'D:\\Temp\\PDF\\'
    if not os.path.exists(path):
        os.makedirs(path)

    urltemplat = 'http://pmmp.cnki.net/Resources/CDDPdf/dis/base/{ks}/{name}.pdf'
    mongo = MongodbCursor()
    cursor = mongo.get_cursor('pmmp_disease', 'url')
    for d in cursor.find({'tree': 1}):
        url = urltemplat.format(ks=d['疾病分类'], name=d['疾病名'])
        path1 = path + '/' + d['疾病分类'] + '/'
        if not os.path.exists(path1):
            os.makedirs(path1)

        filename = path1 + d['疾病名'] + '.pdf'
        if os.path.exists(filename):
            continue

        try:
            time.sleep(2)
            r = requests.get(url)
            if r.status_code != 200:
                print(filename)
                continue
            with open(filename, "wb") as f:  # 开始写文件，wb代表写二进制文件
                f.write(r.content)
        except:
            print(filename)


if __name__ == '__main__':
    # disease(False)
    download_pdf()

