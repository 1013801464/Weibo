import csv
import re
from datetime import datetime

import snownlp

from data_save import DataManage

import libs

def format_date_1(old_date):
    if len(old_date) == 5:  # 日期格式修正(长度为5是不带年份的)
        old_date = "2019-" + old_date
    return old_date


def format_date_2(old_date):
    t = datetime.strptime(old_date, '%a %b %d %H:%M:%S +0800 %Y')
    return datetime.strftime(t, "%Y-%m-%d")


def get_sentiment(text):
    if len(text) > 0:
        s = snownlp.SnowNLP(text)
        return s.sentiments
    else:
        return None


def export_weibo(db_name):
    mblogs = DataManage(db_name).get_mblogs()
    with open('export/tableau/weibo_%s.csv' % db_name, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for mblog in mblogs:
            csv_writer.writerow([mblog['user']['id'], mblog['user']['screen_name'], format_date_1(mblog['created_at']), mblog['comments_count']])


def export_comments_and_childes(db_name):
    with open('export/tableau/comments_%s.csv' % db_name, 'w', newline='', encoding='utf-8') as csvfile:
        comments = DataManage(db_name).get_comments()
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for comment in comments:
            csv_writer.writerow([comment['user']['id'], comment['user']['screen_name'], format_date_2(comment['created_at']), get_sentiment(comment['text']), comment['rootid']])
        childes = DataManage(db_name).get_childes()
        for child in childes:
            csv_writer.writerow([child['user']['id'], child['user']['screen_name'], format_date_2(child['created_at']), get_sentiment(child['text'] if 'reply_original_text' not in child else child['reply_original_text']), child['rootid']])


def export_reposts(db_name):
    with open('export/tableau/reposts_%s.csv' % db_name, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        reposts = DataManage(db_name).get_reposts()
        for repost in reposts:
            csv_writer.writerow([repost['user']['id'], repost['user']['screen_name'], format_date_1(repost['created_at']), get_sentiment(libs.clean_repost_text(repost['raw_text'])), repost['retweeted_status']['id']])


if __name__ == '__main__':
    export_reposts("weibo")
    # export_comments_and_childes("zhuwen")
