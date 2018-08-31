#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie
import json
import random
import traceback

import pymongo

from urllib import request, parse

import requests
from requests.exceptions import ProxyError, ChunkedEncodingError
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from common.property import PROXY_IP2, USER_AGENT
from common.utils import mlogger
from common.utils.common import getNowDate
from common.utils.ip_proxy_pool import GET_PROXY_IP


def getHttpStatus(browser):
    """
    字典值：url,status,statusText
    :param browser:
    :return:
    """
    for responseReceived in browser.get_log('performance'):
        try:
            _json = json.loads(responseReceived[u'message'])
            # [u'message'][u'params'][u'response']
            if 'message' in _json \
                    and 'params' in _json['message'] \
                    and 'response' in _json['message']['params']:
                response = _json['message']['params']['response']

                if response['url'] == browser.current_url \
                        and response['status'] == 200:
                    return True
                    # if response['status'] is not '200':
                    #     return False
        except BaseException as e:
            print(e)
            pass

    return False


def get_user_agent():
    r = ('User-Agent', random.choice(USER_AGENT))
    return r


class Crawler(object):
    """
    1.网络异常
    2.driver怎么判断请求成
    2018-3-27
        1.增加代理，代理需要自己部署
        2.代理更新方法
    """

    def __init__(self, is_proxy):
        """

        :param is_proxy: 是否启用代理
        """
        self.__is_proxy = is_proxy
        self.__log = mlogger.mlog
        self.__mongo = pymongo.MongoClient('192.168.16.113', 27017)
        self.__error_cursor = self.__mongo['minnie']['crawler_error']
        # 驱动器地址
        self.__executable_path = 'C:\\chromedriver.exe'
        # 驱动器日志地址
        self.__service_log_path = 'C:\\Temp\\chromdriver.log'
        # 请求次数达到一定数量，切换代理。
        self.__request_count = 1
        # 浏览器驱动
        self.driver = None
        # request驱动
        self.opener = None

        self.update_proxy()

    def driver_get_url(self, url):
        """
        selenium方式请求，浏览器\n
        请求成功更新url；存储响应的html界面
        :param url: 字符串类型\n
        :return: 长文本
        """

        # if not getHttpStatus(self.driver):
        #     return False

        try:
            self.driver.get(url)
            result = self.driver.page_source
        except TimeoutException as exception:
            result = ''
            error_info = {
                'url': url,
                'type': str(exception),
                'error': traceback.format_exc(),
                'date': getNowDate()
            }
            self.__error_cursor.insert(error_info)

        self.__request_count += 1

        return result

    def request_get_url(self, url, params=None, header=None):
        """
        request方式请求\n
        :param header: 字典格式的header头 \n
        :param url: 字符串格式\n
        :param params: 字典格式\n
        :return: 长文本，或者也可以返回response，建议长文本吧
        """
        headers = {
            'User-Agent': random.choice(USER_AGENT)
        }
        if header is None:
            header = {}
        for key, value in header.items():
            headers[key] = value

        data = None
        if params:
            data = parse.urlencode(params).encode('utf-8')

        r = request.Request(url=self.format_url(url), headers=headers, data=data)
        result = None
        try:
            response = self.opener.open(r)
            result = response.read()
        # except error.HTTPError:
        #     return 'Minnie#400'
        # except IncompleteRead:
        #     logger.error(traceback.format_exc())
        # except RemoteDisconnected:
        #     关闭远程连接
        #     logger.error(traceback.format_exc())
        except BaseException as exception:
            error_info = {
                'url': url,
                'type': str(exception),
                'error': traceback.format_exc(),
                'date': getNowDate()
            }
            self.__error_cursor.insert(error_info)

        self.__request_count += 1

        return result

    @staticmethod
    def format_url(url):
        """
        检测url中是否包含中文，包含中文的话需要编码解码
        将中文转换为二进制
        :param url:
        :return:
        """
        if not url.__contains__('?'):
            return url

        index1 = url.index('?')
        domain = url[0: index1]
        raw_params = url[index1 + 1:]

        format_params = {}
        for p in raw_params.split('&'):
            temp = p.split('=')
            format_params[temp[0]] = temp[1]

        return domain + '?' + str(parse.urlencode(format_params).encode('utf-8').decode('utf-8'))

    def update_proxy(self):
        proxy_ip = GET_PROXY_IP()

        self.__log.info(proxy_ip)
        # 退出
        if self.driver:
            self.driver.quit()
        # 获取新的驱动器
        self.driver = self.new_driver(proxy_ip)

        if proxy_ip:
            # 代理设置
            proxy = request.ProxyHandler(
                {proxy_ip['type']: proxy_ip['ip'] + ':' + str(proxy_ip['port'])})
            self.opener = request.build_opener(request.HTTPHandler, proxy)
        else:
            self.opener = request.build_opener(request.HTTPHandler)
        self.opener.addheaders = [get_user_agent()]
        request.install_opener(opener=self.opener)

    def new_driver(self, proxy_ip=None):
        options = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)

        if proxy_ip:
            options.add_argument(
                '--proxy-server={http}://{ip}:{port}'.format(http=proxy_ip['type'],
                                                             ip=proxy_ip['ip'],
                                                             port=proxy_ip['port']))

        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['loggingPrefs'] = {'performance': 'ALL'}

        if self.__is_proxy:
            driver = webdriver.Chrome(executable_path=self.__executable_path,
                                      desired_capabilities=desired_capabilities,
                                      service_log_path=self.__service_log_path)
        else:
            driver = webdriver.Chrome(executable_path=self.__executable_path,
                                      chrome_options=options,
                                      desired_capabilities=desired_capabilities,
                                      service_log_path=self.__service_log_path)
        driver.implicitly_wait(5)
        return driver

    def refresh(self):
        if self.driver:
            self.driver.refresh()

    def get(self, url, params=None, **kwargs):
        try:
            res = requests.get(url, params=params, proxies=random.choice(PROXY_IP2), **kwargs)
            if res.status_code == 200:
                return res
        except ChunkedEncodingError as chunkedEncodingError:
            self.__log.error(chunkedEncodingError)
        except ConnectionResetError as connectionResetError:
            # 远程主机强迫关闭了一个现有的连接。
            self.__log.error(connectionResetError)
        except ProxyError as proxyerror:
            self.__log.error(proxyerror)
        except ConnectionError as connectionError:
            self.__log.error(connectionError)
        except BaseException:
            self.__log.error(traceback.format_exc())
        return False
