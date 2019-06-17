import re
from datetime import datetime

import snownlp


def read_stop_words():
    """
    读取停用词
    :return:
    """
    stop_words = set()
    with open(r"stopwords.txt", 'r', encoding='utf-8') as f:
        for line in f.readlines():
            stop_words.add(line.strip('\n'))
    return stop_words


def replace_img_tag(m):
    """
    将这样的html tag
    <img alt=[思考] src="//h5.sinaimg.cn/m/emoticon/icon/default/d_sikao-7f3b022e72.png" style="width:1em; height:1em;" />
    提取出alt
    :param m:
    :return:
    """
    result = re.findall(r'((?<=alt=).*?(?= ))', m.string[m.start():m.end()])  # 提取出前面是alt=后面是空格的内容
    if len(result) > 0:
        return result[0]
    else:
        return ''


def remove_links(text):
    """
    删除无用的URL链接
    :param text: 待处理的文本
    :return: 删除链接后的文本
    """
    text = re.sub(r'<img .*?/>', replace_img_tag, text)  # 移除表情
    text = re.sub(r'<(?=[a-z/]).*?>', '', text)  # 移除其中的其它HTML标签
    return text


def npy_reader(file, save=False):
    import numpy as np
    if not "".endswith(".npy"): file += ".npy"
    var = np.load(file)
    print(var)
    if save:
        import csv
        with open(file + ".csv", 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in range(var.shape[0]):
                if var[i, 0] in stop_words or len(var[i, 0]) < 2: continue
                csv_writer.writerow([var[i, 0], var[i, 1]])
    return var


def compare(file1, file2):
    a = npy_reader(file1)
    b = npy_reader(file2)
    a_set = set()
    b_set = set()
    for i in range(a.shape[0]):
        if int(a[i, 1]) < 4 or a[i, 0] in stop_words or len(a[i, 0]) < 2: continue
        a_set.add(a[i, 0])
    for i in range(b.shape[0]):
        if int(b[i, 1]) < 2 or b[i, 0] in stop_words or len(b[i, 0]) < 2: continue
        b_set.add(b[i, 0])
    d = a_set.difference(b_set)
    return d.intersection(b_set)


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


def clean_repost_text(text):
    if text in ('转发微博', '轉發微博', '转发', 'Repost'):
        return ''
    else:
        result = re.findall(r'([^/]*?)(?://@.*?:)', text)
        return result[0] if len(result) > 0 else text


def calculate_emotions(name):
    """
    计算评论 子评论 转发的情感值(将结果写到数据库里)
    """
    from data_save import DataManage
    dm = DataManage(to_db_name(name))
    comments = dm.get_comments()
    for comment in comments:
        sent = get_sentiment(comment['text'])
        if sent is not None:
            comment['sentiment'] = sent
            dm.save_comment(comment)
    childes = dm.get_childes()
    for child in childes:
        sent = get_sentiment(child['text'] if 'reply_original_text' not in child else child['reply_original_text'])
        if sent is not None:
            child['sentiment'] = sent
            dm.save_child_comment(child)
    reposts = dm.get_reposts()
    for repost in reposts:
        sent = get_sentiment(clean_repost_text(repost['raw_text']))
        if sent is not None:
            repost['sentiment'] = sent
            dm.save_repost(repost)


import hashlib



def to_db_name(name):
    """
    求字符串的MD5码, 作为数据库的名字
    """
    hl = hashlib.md5()          # 创建md5对象(必须每次都创建)
    print('MD5之前' + name)
    hl.update(name.encode('utf-8'))
    return 'DB%s' % hl.hexdigest()

if __name__ == '__main__':
    print(to_db_name('基因编辑婴儿'))
    # calculate_emotions("zhuwen")
