#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie
# 医脉通
import csv

import time

from common.base_crawler import BaseCrawler


class yaozh_yaopinzhongbiao(BaseCrawler):
    """
    药智网 药品中标信息
    """
    def pushMail(self):
        pass

    def _get_cn_name(self):
        return '药智网-药品中标信息'

    def _get_name(self):
        return '药智网-药品中标信息'

    def _init_url(self):
        url = 'https://db.yaozh.com/index.php/Yaopinzhongbiao/index?dbname=yaopinzhongbiao&name={' \
              'name}' \
              '&first=%E5%85%A8%E9%83%A8&pageSize=30&p=1&list_order=me_approvaldate'
        result_list = []

        csv_reader = csv.reader(open('C:\Temp\药品通用名.csv', encoding='utf-8'))
        for row in csv_reader:
            result_list.append({
                'url': url.format(name=row[0]),
                'type': self._get_cn_name(),
                'drugName': row[0],
                'count': 0,
                'tree': 1
            })
        return result_list

    def request(self, d):
        self._crawler.driver_get_url("https://db.yaozh.com/")

        key = ['药品通用名', '商品名', '剂型', '规格', '包装转比', '单位', '中标价', '质量层次', '生产企业',
               '投标企业', '中标省份', '发布日期', '备注', '来源']
        # 加载页面
        html = self._crawler.driver_get_url(d['url'])
        time.sleep(0.5)
        # soup化
        soup = self.to_soup(html)
        # 获取数据所在位置，进行验证确认。
        tbody = soup.find_all('tbody')
        # 校验：校验通过存储数据，继续；校验失败，跳过
        if tbody and len(tbody) >= 1:
            # 存储详情页链接，直接存储data中去
            for tr in tbody[0].find_all('tr'):
                data = {}
                for i, td in enumerate(tr.find_all('td')[1: 15]):
                    data[key[i]] = td.text
                    if i == 13:
                        a = td.find('a')
                        if a and a['href']:
                            data['source_url'] = a['href']
                self._data_cursor.insert(data)
        else:
            # 无效链接
            self._urlpool.update({'_id': d['_id']}, {'$set': {'isenable': '3'}})
            return False, ''

        # 如果是第一页的话，需要检测是否还有下一页
        page = soup.find('span', class_='total-nums')
        if page and d['tree'] == 1:
            url = d['url']
            count = int(reg('[0-9]+', page.text))
            self._urlpool.update({'url': url}, {'$set': {'count': count}})

            if 30 < count:
                self.log.info(d['drugName'] + ' >> ' + str(count))
                self._urlpool.put({
                    'url': url.replace('p=1', 'p=2'),
                    'type': self._cn_name,
                    'drugName': d['drugName'],
                    'tree': 2
                })
            if 60 < count:
                self._urlpool.put({
                    'url': url + '%20desc',
                    'type': self._cn_name,
                    'drugName': d['drugName'],
                    'tree': 2
                })
            if count > 90:
                self._urlpool.put({
                    'url': url.replace('p=1', 'p=2') + '%20desc',
                    'type': self._cn_name,
                    'drugName': d['drugName'],
                    'tree': 2
                })

        return True, html

    def parser(self, d):
        pass
