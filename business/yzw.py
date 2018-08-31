#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie
# 医脉通
import csv
import random

import time

from selenium.common.exceptions import NoSuchElementException

from common.base_crawler import BaseCrawler
from common.utils.common import reg


class yaozh(BaseCrawler):
    def __init__(self):

        self._users = [{
            'username': 'qiushengming@aliyun.com',
            'pwd': 'qd7qrjm3'
        }, {
            'username': '583853240@qq.com',
            'pwd': 'bjjtq4cn'
        }]
        super().__init__()

    def logout(self):
        self._crawler.driver_get_url(
            'https://www.yaozh.com/login/logout/?backurl=http%3A%2F%2Fwww.yaozh.com%2F')
        time.sleep(4)

    def login(self):
        """
        登陆
        是否要切换登陆
        username = qiushengming@aliyun.com
        password = qd7qrjm3
        地址：https://www.yaozh.com/login
        :return:
        """

        self.logout()

        temp_user = random.choice(self._users)
        driver = self._crawler.driver

        # Client in temporary black list
        # 建议发邮件进行报告
        if driver.find_element_by_xpath('/html/body').text == 'Client in temporary black list':
            time.sleep(100)
            return

        driver.get('https://db.yaozh.com/')
        time.sleep(10)

        driver.get('https://www.yaozh.com/login')

        username = driver.find_element_by_id('username')
        username.send_keys(temp_user['username'])
        password = driver.find_element_by_id('pwd')
        password.send_keys(temp_user['pwd'])
        login_button = driver.find_element_by_id('button')
        login_button.click()
        timeout = 2

        while True:
            try:
                driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/a[1]')
                break
            except NoSuchElementException:
                self.log.info('登陆中，请等待')
            time.sleep(timeout)
            timeout += 2

            if timeout > 10:
                self.log.error('链接超时！！')
                return False

        self.log.info('登陆成功')
        return True


class yaozh_yaopinzhongbiao(yaozh):
    """
    药智网 药品中标信息
    """
    def __init__(self):
        self.is_login = True
        super().__init__()

    def pushMail(self):
        pass

    def _get_cn_name(self):
        return '药智网-药品中标信息'

    def _get_name(self):
        return '药智网-药品中标信息'

    def _init_url(self):
        # if self._urlpool.find_all_count():
        #     return
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
        if self.is_login:
            self.is_login = False
            self.login()

        key = ['药品通用名', '商品名', '剂型', '规格', '包装转比', '单位', '中标价', '质量层次', '生产企业',
               '投标企业', '中标省份', '发布日期', '备注', '来源']
        # 加载页面
        html = self._crawler.driver_get_url(d['url'])
        time.sleep(5)
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
            # 因为返回False后，浏览器会重新创建并且数据会不一致的
            self.is_login = True
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
