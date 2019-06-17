import datetime
import json

import jieba
from flask import Flask, request

import non_net_analyze
from data_save import DataManage
import libs
# app = Flask(__name__)
db = {}
default_db = 'weibo'
app = Flask(__name__, static_url_path='', root_path='.')


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/hot_words')
def get_hot_words():
    keyword = request.args.get('key', type=str, default=default_db)
    return non_net_analyze.get_hot_words(libs.to_db_name(keyword))


@app.route('/basic_info')
def get_basic_info():
    keyword = request.args.get('key', type=str, default=default_db)
    return non_net_analyze.get_basic_info(libs.to_db_name(keyword))


@app.route('/comment_emotion')
def get_comment_emotion():
    keyword = request.args.get('key', type=str, default=default_db)
    return non_net_analyze.get_comment_emotion(libs.to_db_name(keyword))


@app.route('/repost_emotion')
def get_repost_emotion():
    keyword = request.args.get('key', type=str, default=default_db)
    return non_net_analyze.get_repost_emotion(libs.to_db_name(keyword))


@app.route('/new_analyze')
def new_analyze_task():
    # 然后libs.calculate_emotions
    import crawler
    keyword = request.args.get('key', type=str, default=default_db)
    crawler.execute(keyword)            # 首先爬虫
    libs.calculate_emotions(keyword)    # 计算情感值
    # import network_analyze
    # network_analyze.execute(keyword)  # 网络分析(有需要时使用)

## 旧代码
@app.route('/weibo_count/<frequency>')
def get_weibo_count(frequency):
    data_save = DataManage(request.args.get('db', type=str, default=default_db))    # TODO hash
    frequency = int(frequency)
    count = {}
    weibos = data_save.get_mblogs()
    # 统计每个日期有多少条微博
    for weibo in weibos:
        if len(weibo['created_at']) == 5:  # 日期格式修正
            weibo['created_at'] = "2019-" + weibo['created_at']
        if weibo['created_at'] not in count:
            count[weibo['created_at']] = [1, weibo['comments_count']]
        else:
            count[weibo['created_at']][0] += 1
            count[weibo['created_at']][1] += weibo['comments_count']
    # 求出微博的最大日期和最小日期
    min_date_str = min(count)
    max_date_str = max(count)
    min_date = datetime.datetime.strptime(min_date_str, "%Y-%m-%d")
    max_date = datetime.datetime.strptime(max_date_str, "%Y-%m-%d")
    # 从最小日期开始循环, 每次日期+1天
    i = min_date
    group_time = ""
    group_seq = frequency
    count2 = {}
    while i <= max_date:
        time_str = i.strftime("%Y-%m-%d")  # 输出为2019-01-11这种的字符串
        if group_seq == frequency:  # 如果满一组, 进行进行相关初始化操作
            group_seq = 0
            group_time = time_str
            if group_time not in count2:
                count2[group_time] = [0, 0]
        if time_str in count:
            count2[group_time][0] += count[time_str][0]
            count2[group_time][1] += count[time_str][1]
        i = i + datetime.timedelta(days=1)
        group_seq += 1
    result = {}
    result["time"] = []
    result["weibo"] = []
    result["comment"] = []
    for c in count2:
        result["time"].append(c)
        result["weibo"].append(count2[c][0])
        result["comment"].append(count2[c][1])
    return json.dumps(result)


@app.route('/comment_distribution')
def get_comment_distribution():
    data_save = DataManage(request.args.get('db', type=str, default=default_db))
    weibos = data_save.get_mblogs()
    pairs = {}
    for weibo in weibos:
        if weibo['comments_count'] not in pairs:
            pairs[weibo['comments_count']] = 1
        else:
            pairs[weibo['comments_count']] += 1
    result = []
    s = sorted(pairs)
    for i in s:
        result.append([i, pairs[i]])
    return json.dumps({"all": result}, ensure_ascii=False)


@app.route('/comment_of_each_user')
def get_comment_of_each_user():
    data_save = DataManage(request.args.get('db', type=str, default=default_db))
    count = {}
    comments = data_save.get_comments()
    for comment in comments:
        if comment['user']['id'] in count:
            count[comment['user']['id']][1] += 1
        else:
            count[comment['user']['id']] = [comment['user']['screen_name'], 1]
    childes = data_save.get_childes()
    for child in childes:
        if child['user']['id'] in count:
            count[child['user']['id']][1] += 1
        else:
            count[child['user']['id']] = [child['user']['screen_name'], 1]
    result = []
    others = 0
    for c in count:
        if count[c][1] == 1:
            others += 1
        else:
            result.append({"name": count[c][0], "value": count[c][1]})
    result.append({"name": "其它", "value": others})
    result.sort(key=lambda x: x["value"], reverse=True)
    return json.dumps(result, ensure_ascii=False)


@app.route('/comment_of_each_user/<freq>')
def get_comment_of_each_user_with_freq(freq):
    pass


if __name__ == '__main__':
    jieba.initialize()                  # 初始化分词程序
    app.run(host='127.0.0.1', port=5000, debug=True)    # 启动服务器
