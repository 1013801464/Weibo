"""
爬虫程序
"""
import json
import re
import time
import urllib.parse

import requests
from selenium import webdriver

import libs
from data_save import DataManage

keyword = ''
# db_name = 'zhuwen'

r = requests.Session()
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0'}

PART_OF_WEIBO_API_URL = urllib.parse.quote('type=1&q=#%s#&t=0' % keyword)  # 有时候type=61才可用
WEIBO_API_URL = r'https://m.weibo.cn/api/container/getIndex?containerid=100103' + PART_OF_WEIBO_API_URL + '&page_type=searchall'
COMMENT_API_URL1 = r'https://m.weibo.cn/comments/hotflow?id=%s&mid=%s&max_id_type=0'
COMMENT_API_URL2 = r'https://m.weibo.cn/comments/hotflow?id=%s&mid=%s&max_id=%s&max_id_type=0'
COMMENT_CHILD_API_URL1 = r'https://m.weibo.cn/comments/hotFlowChild?cid=%s&max_id=0&max_id_type=0'
COMMENT_CHILD_API_URL2 = r'https://m.weibo.cn/comments/hotFlowChild?cid=%s&max_id=%s&max_id_type=0'
REPOST_API_URL = r'https://m.weibo.cn/api/statuses/repostTimeline?id=%s&page=%s'


def refresh_api():
    global PART_OF_WEIBO_API_URL
    global WEIBO_API_URL
    global COMMENT_CHILD_API_URL2
    global COMMENT_CHILD_API_URL1
    global COMMENT_API_URL1
    global COMMENT_API_URL2
    global REPOST_API_URL
    PART_OF_WEIBO_API_URL = urllib.parse.quote('type=1&q=#%s#&t=0' % keyword)  # 有时候type=61才可用
    WEIBO_API_URL = r'https://m.weibo.cn/api/container/getIndex?containerid=100103' + PART_OF_WEIBO_API_URL + '&page_type=searchall'
    COMMENT_API_URL1 = r'https://m.weibo.cn/comments/hotflow?id=%s&mid=%s&max_id_type=0'
    COMMENT_API_URL2 = r'https://m.weibo.cn/comments/hotflow?id=%s&mid=%s&max_id=%s&max_id_type=0'
    COMMENT_CHILD_API_URL1 = r'https://m.weibo.cn/comments/hotFlowChild?cid=%s&max_id=0&max_id_type=0'
    COMMENT_CHILD_API_URL2 = r'https://m.weibo.cn/comments/hotFlowChild?cid=%s&max_id=%s&max_id_type=0'
    REPOST_API_URL = r'https://m.weibo.cn/api/statuses/repostTimeline?id=%s&page=%s'


class Broswer:
    def __init__(self):
        self.browser = webdriver.Chrome()
        self.browser.get('https://passport.weibo.cn/signin/login')  # 进入登录
        input("登录成功后请按回车")

    def get_comments(self, id, mid, with_child=False):
        """
        获取某个微博的(所有)评论
        :param id: 博客id
        :param mid: 博客mid
        :param with_child: 是否顺便爬一下子评论
        :return:
        """
        ok = 1
        first = True
        max_id = -1
        while ok == 1 and max_id != 0:
            time.sleep(1)
            if first:
                self.browser.get(COMMENT_API_URL1 % (id, mid))
                first = False
            else:
                self.browser.get(COMMENT_API_URL2 % (id, mid, max_id))
            result = self.browser.find_element_by_xpath('html').text
            result = json.loads(result)
            ok = result['ok']
            if ok != 1: break  # ok表示本次查询的结果是否成功
            max_id = result['data']['max_id']
            for comment in result['data']['data']:
                comment['rootid'] = id  # 修改rootid为帖子的id, 原来的rootid没啥用
                comment['text'] = re.sub(r'<img .*?/>', libs.replace_img_tag, comment['text'])  # 移除表情
                comment['text'] = re.sub(r'<(?=[a-z/]).*?>', '', comment['text'])  # 移除其中的其它HTML标签
                dm.save_comment(comment)

                if with_child and comment['total_number'] > 0:
                    time.sleep(2)
                    self.get_child_comments(comment['id'])
            time.sleep(2)

    def get_child_comments(self, comment_id):
        """
        获取评论下面的子评论
        :param comment_id: 评论的ID
        :return:
        """
        ok = 1
        first = True
        max_id = -1
        while ok == 1 and max_id != 0:
            if first:
                self.browser.get(COMMENT_CHILD_API_URL1 % comment_id)
                first = False
            else:
                self.browser.get(COMMENT_CHILD_API_URL2 % (comment_id, max_id))
            result = self.browser.find_element_by_xpath('html').text
            if result == '暂无数据': break
            result = json.loads(result)
            ok = result['ok']
            if ok != 1: break
            max_id = result['max_id']
            for child in result['data']:
                child['text'] = re.sub(r'<img .*?/>', libs.replace_img_tag, child['text'])  # 移除表情
                child['text'] = re.sub(r'<(?=[a-z/]).*?>', '', child['text'])  # 移除其中的其它HTML标签
                dm.save_child_comment(child)
            time.sleep(3)

    def get_reposts(self, id):
        page = 1
        while True:
            self.browser.get(REPOST_API_URL % (id, page))
            result = self.browser.find_element_by_xpath('html').text
            result = json.loads(result)
            ok = result['ok']
            if ok != 1: break
            for repost in result['data']['data']:
                dm.save_repost(repost)
            time.sleep(3.5)
            if page == result['data']['max']: break
            page += 1


def get_mblogs():
    """
    获取跟话题相关的微博
    :return:
    """
    weibo_url = (WEIBO_API_URL + ('' if x == 1 else '&page=' + str(x)) for x in range(1, 1000)) # TODO page=0的时候可能有问题
    print(next(weibo_url))
    k = 0
    for i in range(1000):
        result = r.get(next(weibo_url), headers=headers).text
        result = json.loads(result)
        if result['ok'] == 0: break
        cards = result['data']['cards']
        for card in cards:
            for c in card['card_group']:
                print('%s-%s' % (k, i))
                if 'mblog' not in c: continue
                mblog = c['mblog']  # 把mblog存下来就可以了
                mblog['text'] = re.sub(r'<img .*?/>', libs.replace_img_tag, mblog['text'])
                mblog['text'] = re.sub(r'<(?=[a-z/]).*?>', '', mblog['text'])
                dm.save_mblog(mblog)
                k += 1
        time.sleep(3)


def get_comments(b):
    mblogs = dm.get_mblogs()
    for blog in mblogs:
        if blog['comments_count'] == 0: continue
        b.get_comments(blog['id'], blog['mid'], with_child=True)


def get_comments_of_reposts(b):
    reposts = dm.get_reposts()
    for repost in reposts:
        if repost['comments_count'] == 0: continue
        b.get_comments(repost['id'], repost['mid'], with_child=True)


def get_reposts(b):
    mblogs = dm.get_mblogs()
    for blog in mblogs:
        if blog['reposts_count'] == 0: continue
        b.get_reposts(blog['id'])


dm = None


def execute(name):
    global dm
    global keyword
    keyword = name
    refresh_api()
    dm = DataManage(libs.to_db_name(name))
    get_mblogs()  # 获得微博正文
    b = Broswer()  # 打开浏览器
    get_reposts(b)  # 获得转发的内容
    get_comments(b)  # 获得微博的评论(及子评论)
    get_comments_of_reposts(b)  # 获得转发的微博的评论(及子评论)


if __name__ == '__main__':
    execute("王俊凯")
