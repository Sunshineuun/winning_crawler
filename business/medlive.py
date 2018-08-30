#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie
# 医脉通
import re
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from common.base_crawler import BaseCrawler
from common.property import EMIAL_HOST, EMIAL_SYS_PW, EMIAL_SYS
from common.utils.common import getNowDate
from common.utils.excel import WriteXLSXCustom


class crawler2YMT(BaseCrawler):
    """
    超说明书用药-医脉通指南-http://guide.medlive.cn/
        *超说明书*
        *超药物说明书*
        *超药品说明书*
    """

    def __init__(self, ip=None):
        self.key = '*超说明书*,*超药物说明书*,*超药品说明书*'.split(',')
        self.email_msg = []
        self.start_date = getNowDate()
        super().__init__(ip)

    def _get_cn_name(self):
        return '医脉通指南'

    def _get_name(self):
        return '医脉通指南-超说明书用药'

    def _init_url(self):
        result = []
        url = 'http://guide.medlive.cn/search?q={q}&search_type=&sort=time'
        for k in self.key:
            result.append({
                'url': url.format(q=k.replace('*', '')),
                'type': self._get_cn_name(),
                'key': k
            })
        return result

    def request(self, d):
        html = ''
        try:
            html = self._crawler.driver_get_url(d['url'])
            soup = self.to_soup(html)
            divs = soup.find_all('div', class_='center_guide')
            # 处理当前页的列表
            for div in divs:
                ps = div.find_all('p')
                title = ps[0].a.text
                data = {
                    '名称': self._get_cn_name(),
                    'KEY': d['key'],
                    '标题': title,
                    'URL': ps[0].a['href'],
                    '父URL': d['url'],
                    '创建时间': getNowDate()
                }
                # 判断日期是否在昨天之后 or 程序启动之后

                # 包含KEY & URL没有在历史里面出现，就发送邮件
                for k in self.key:
                    if re.search(k.replace('*', '.*'), title) \
                            and self._history.count({'URL': data['URL']}) == 0:
                        self.email_msg.append(data)

                # 存储历史
                self._history.insert(data)
            # 判断是否需要进行翻页
            spans = soup.find_all('span', class_='flip_total')
            # 有翻页的工具栏 & 链接中不包含翻页参数
            if len(spans) and d['url'].find('&page=') == -1:
                page = int(spans[0].text.split(' ')[1])
                # 翻页从0开始
                for p in range(1, page):
                    self._urlpool.save_url({
                        'url': d['url'] + '&page=' + str(p),
                        'type': self._get_cn_name(),
                        'key': d['key']
                    })
                    # 当URL在今天队列中，就不再加入
                    # today_minTime = dt.datetime.combine(datetime.now(), dt.time.min)
                    # 条件 = {'insert_date': {'$gt': today_minTime}, 'url': d1['url']}
                    # if self._urlpool.cursor.find(条件).count() <= 0:

            return True, html
        except BaseException as e:
            # div获取不到捕获异常，将错误日志及其网页内容捕获以附件的形式发送出来。
            print(str(d) + self.get_traceback() + '\n' + html)
            content = '当前请求：\n{}\n错误信息：\n{}'.format(str(d), self.get_traceback())
            affix = {
                'filename': '下载的HTML文件',
                'content': html
            }
            receiver = 'qiushengming@aliyun.com'
            self.send_error_email(content=content, affix=affix, receiver=receiver)

            self.log.error(d)
            self.log.error(self.get_traceback())
            self.log.error(html)
        return False, html

    def parser(self, d):
        return True

    def get_excel(self):
        """
        家族
        :return:
        """
        content = self.email_msg

        title = ['名称', 'KEY', '标题', 'URL']

        path = '\\excel\\{}_{}'.format(datetime.now().strftime('%Y-%m-%d %H'),
                                       self._get_name())
        write = WriteXLSXCustom(path)

        rowindex = 0
        write.write(rowindex, title)

        for d in content:
            rowindex += 1
            row = []
            for k in title:
                if k in d:
                    row.append(d[k])
                else:
                    row.append('')
            write.write(rowindex, row)

        write.close()
        return write.path

    def pushMail(self):
        # content = ''
        # for m in self.email_msg:
        #     for k, v in m.items():
        #         content += '{}:{} | '.format(k, v)
        #     content += '\n'

        if not self.email_msg:
            self.log.info('无数据更新')
            return

        path = self.get_excel()

        msg = MIMEMultipart()
        msg['Subject'] = self._get_cn_name() + '更新通知'  # 主题
        msg['From'] = '爬虫系统'  # 发件人昵称
        msg['To'] = 'qiushengming'  # 收件人昵称

        # 正文
        """
            站点名称：
            搜索关键字：self.key.join(',')
            搜索结果：共计N条
            搜索结果详报：path
        """
        正文 = '站点名称：{zd}\n搜索关键字：{key}\n搜索结果统计：共计{count}条\n搜索结果详报：{fn}'.format(
            zd=self._get_cn_name(),
            fn=path.split('\\')[-1],
            key=','.join(self.key),
            count=len(self.email_msg))
        msg.attach(MIMEText(正文, 'plain', 'utf-8'))

        xlsxpart = MIMEApplication(open(path, 'rb').read())
        # 注意：此处basename要转换为gbk编码，否则中文会有乱码。
        xlsxpart.add_header('Content-Disposition', 'attachment',
                            filename=('gbk', '', path.split('\\')[2]))
        msg.attach(xlsxpart)
        # 发送
        smtp = smtplib.SMTP()
        smtp.connect(EMIAL_HOST, 25)
        smtp.login(EMIAL_SYS, EMIAL_SYS_PW)
        smtp.sendmail(EMIAL_SYS, 'wangfumin@tech-winning.com', msg.as_string())
        smtp.quit()


if __name__ == '__main__':
    crawler2YMT()
