#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie

# 疾病
from bs4 import BeautifulSoup
from bs4 import Tag
from selenium.webdriver.support.select import Select

from common.base_crawler import BaseCrawler
from common.utils.common import readFile


class disease(BaseCrawler):
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
        key = ['疾病名', '英文名', '别名', '疾病分类', 'ICD号']
        html = self._crawler.driver_get_url(d['url'])
        if (d['tree']) == 0:
            driver = self._crawler.driver
            # 获取并点击提交按钮
            submit = driver.find_element_by_id('DS_Basic1_btnSubmit')
            submit.click()
            # 改变每页显示的数量
            pageCount = Select(driver.find_element_by_id('DS_Basic1_btnSubmit'))
            pageCount.select_by_index(2)

            # 下一页按钮
            nextButton = driver.find_element_by_id('DS_Basic1_linkNext')
            while not nextButton['disabled']:
                # 获取当前页面数据
                soup = self.to_soup(driver.page_source)
                trs = soup.find('table', id='DS_Basic1_listResult').find('table').find_all('tr')
                for tr in trs[1:]:
                    tds = tr.find_all('td')
                    # 当tr中只有一个td的时候
                    if len(tds) == 1:
                        continue
                    row = {
                        'url': 'http://pmmp.cnki.net/cdd/Disease' + tds[1].a['href'],
                        'tree': 1
                    }
                    for i, td in enumerate(tds[1:]):
                        row[key[i]] = td.text
                    self._urlpool.save_url(row)
                nextButton.click()
                nextButton = driver.find_element_by_id('DS_Basic1_linkNext')
        elif (d['tree']) == 1:
            soup = self.to_soup(html)
            trs = soup.find('td', class_='style8').find_all('tr')
            for i, tr in enumerate(trs):
                pass

    def _get_name(self):
        pass

    def _get_cn_name(self):
        pass

if __name__ == '__main__':
    html = readFile('D:\\Temp\\1.html')
    soup = BeautifulSoup(html, 'html.parser')
    td = soup.find('td', class_='style8')
    trs = td.table.tbody.contents
    trs1 = []
    for tr in trs:
        if type(tr) == Tag:
            trs1.append(tr)

    for tr in trs1:
        pass


    print(1)
