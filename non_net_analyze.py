import json
from collections import defaultdict
from datetime import datetime
from datetime import timedelta

import jieba

import libs
from data_save import DataManage

stop_words = libs.read_stop_words()


def get_hot_words(db_name):
    """
    返回词语频率Top 50的词语及出现次数; 用于字符云
    :param db_name: 数据库名
    :return: json.dumps生成的字符串
    """
    weibos = DataManage(db_name).get_mblogs()
    word_count = defaultdict(int)  # 词语到数量的映射
    for weibo in weibos:
        text = weibo['longText']['longTextContent'] if weibo['isLongText'] else weibo['text']
        seg_list = jieba.cut_for_search(text)  # 对每个评论的内容分词
        for word in seg_list:
            if len(word) < 2 or word in stop_words: continue  # 去除过短或没用的词
            word_count[word] += 1
    import operator
    w = sorted(word_count.items(), key=operator.itemgetter(1), reverse=True)
    length = min([50, len(word_count)])
    result = []
    for i in range(length):
        result.append({"name": w[i][0], "value": w[i][1]})
    return json.dumps(result, ensure_ascii=False)


def get_basic_info(db_name):
    """
    获得下面的4个变量: 微博总量、转发总量、评论总量、点赞总量
    :param db_name: 数据库名称
    :return: Json.Dumps生成个的字符串
    """
    weibos = DataManage(db_name).get_mblogs()
    weibo_count = 0  # 微博数量
    reposts_count = 0  # 转发量
    comments_count = 0  # 评论量
    attitudes_count = 0  # 点赞量
    for weibo in weibos:
        weibo_count += 1
        reposts_count += weibo['reposts_count']
        comments_count += weibo['comments_count']
        attitudes_count += weibo['attitudes_count']
    return json.dumps({"weibo": weibo_count, "reposts": reposts_count, "comments": comments_count, "attitudes": attitudes_count})


def get_comment_emotion(db_name):
    comments = DataManage(db_name).get_comments()
    min_date_str = '9999-99-99'
    max_date_str = '0000-00-00'
    positive = defaultdict(int)
    neutral = defaultdict(int)
    negative = defaultdict(int)
    number = defaultdict(int)
    for comment in comments:
        date_str = libs.format_date_2(comment['created_at'])
        number[date_str] += 1
        if 'sentiment' not in comment: continue
        sent = comment['sentiment']
        if sent < 1 / 3:
            negative[date_str] += 1
        elif sent > 2 / 3:
            positive[date_str] += 1
        else:
            neutral[date_str] += 1
        if date_str < min_date_str:
            min_date_str = date_str
        elif date_str > max_date_str:
            max_date_str = date_str
    childes = DataManage(db_name).get_childes()
    for child in childes:
        date_str = libs.format_date_2(child['created_at'])
        number[date_str] += 1
        if 'sentiment' not in child: continue
        sent = child['sentiment']
        if sent < 1 / 3:
            negative[date_str] += 1
        elif sent > 2 / 3:
            positive[date_str] += 1
        else:
            neutral[date_str] += 1
        if date_str < min_date_str:
            min_date_str = date_str
        elif date_str > max_date_str:
            max_date_str = date_str
    min_date = datetime.strptime(min_date_str, "%Y-%m-%d")
    max_date = datetime.strptime(max_date_str, "%Y-%m-%d")
    i = min_date
    time_list = []
    positive_list = []
    neutral_list = []
    negative_list = []
    number_list = []
    while i <= max_date:
        time_str = i.strftime("%Y-%m-%d")
        time_list.append(time_str)
        number_list.append(number[time_str])
        positive_list.append(positive[time_str])
        neutral_list.append(neutral[time_str])
        negative_list.append(negative[time_str])
        i = i + timedelta(days=1)
    result = {'time': time_list, 'number': number_list, 'positive': positive_list, 'neutral': neutral_list, 'negative': negative_list}
    return json.dumps(result)


def get_repost_emotion(db_name):
    reposts = DataManage(db_name).get_reposts()
    min_date_str = '9999-99-99'
    max_date_str = '0000-00-00'
    positive = defaultdict(int)
    neutral = defaultdict(int)
    negative = defaultdict(int)
    number = defaultdict(int)
    for repost in reposts:
        date_str = libs.format_date_1(repost['created_at'])
        number[date_str] += 1
        if 'sentiment' not in repost: continue
        sent = repost['sentiment']
        if sent < 1 / 3:
            negative[date_str] += 1
        elif sent > 2 / 3:
            positive[date_str] += 1
        else:
            neutral[date_str] += 1
        if date_str < min_date_str:
            min_date_str = date_str
        elif date_str > max_date_str:
            max_date_str = date_str
    min_date = datetime.strptime(min_date_str, "%Y-%m-%d")
    max_date = datetime.strptime(max_date_str, "%Y-%m-%d")
    i = min_date
    time_list = []
    positive_list = []
    neutral_list = []
    negative_list = []
    number_list = []
    while i <= max_date:
        time_str = i.strftime("%Y-%m-%d")
        time_list.append(time_str)
        number_list.append(number[time_str])
        positive_list.append(positive[time_str])
        neutral_list.append(neutral[time_str])
        negative_list.append(negative[time_str])
        i = i + timedelta(days=1)
    result = {'time': time_list, 'number': number_list, 'positive': positive_list, 'neutral': neutral_list, 'negative': negative_list}
    return json.dumps(result)


if __name__ == '__main__':
    print(get_comment_emotion("weibo"))
