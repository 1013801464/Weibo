import csv
from collections import defaultdict
from datetime import datetime
from datetime import timedelta

import jieba
import networkx as nx

import libs
from data_save import DataManage

class ReplyNetwork:
    """
    由回复关系组建的用户网络
    """

    def __init__(self, db_name):
        self.name = db_name
        self.db = DataManage(db_name)

    def export_to_file(self):
        """
        导出用户的回复关系, 以用户ID呈现.
        :return: 直接输出到edges_dbname.csv中了
        """
        print(self.name)
        blog_to_user_id = {}  # 存储微博到用户ID的映射, 为之后的评论建边用
        comment_to_user_id = {}  # 存储评论到用户ID的映射, 为之后的子评论建边用
        mblogs = self.db.get_mblogs()
        for mblog in mblogs:  # 获得微博到用户ID的映射
            if mblog['comments_count'] > 0:
                blog_to_user_id[mblog['id']] = mblog['user']['id']
        reposts = self.db.get_reposts()
        for repost in reposts:
            if repost['comments_count'] > 0:
                blog_to_user_id[repost['id']] = repost['user']['id']
        with open('export/reply_network/edges_%s.csv' % self.name, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            comments = self.db.get_comments()
            for comment in comments:
                try:
                    csv_writer.writerow([comment['user']['id'], blog_to_user_id[comment['rootid']], datetime.strftime(datetime.strptime(comment['created_at'], '%a %b %d %H:%M:%S %z %Y'), '%Y-%m-%d')])
                except KeyError:
                    pass
                comment_to_user_id[comment['id']] = comment['user']['id']
            child_comments = self.db.get_childes()
            for child in child_comments:
                csv_writer.writerow([child['user']['id'], comment_to_user_id[child['rootid']], datetime.strftime(datetime.strptime(child['created_at'], '%a %b %d %H:%M:%S %z %Y'), '%Y-%m-%d')])

    def load_network(self, analyze_func):
        G = nx.DiGraph()  # DiGraph是有向图
        with open('export/reply_network/edges_%s.csv' % self.name, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for edge in csv_reader:
                a = int(edge[0])
                b = int(edge[1])
                if G.has_edge(a, b):
                    G.add_edge(a, b, weight=G.get_edge_data(a, b)['weight'] + 1)
                else:
                    G.add_edge(a, b, weight=1)
        analyze_func(G, "回复关系网络")

    def load_network_with_period(self, analyze_func, period=1):
        min_date_str = '9999-99-99'
        max_date_str = '0000-00-00'
        with open('export/reply_network/edges_%s.csv' % self.name, 'r', newline='', encoding='utf-8') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for edge in spamreader:
                d = edge[2]
                if d < min_date_str:
                    min_date_str = d
                elif d > max_date_str:
                    max_date_str = d
        min_date = datetime.strptime(min_date_str, "%Y-%m-%d")
        max_date = datetime.strptime(max_date_str, "%Y-%m-%d")
        i = min_date  # i是datetime类型的循环变量
        while i <= max_date:  # 从最小日期开始循环, 每次日期+周期天
            low = i.strftime("%Y-%m-%d")  # 输出为2019-01-11这种的字符串
            i = i + timedelta(days=period)
            high = i.strftime("%Y-%m-%d")
            G = nx.DiGraph()
            with open('export/reply_network/edges_%s.csv' % self.name, 'r', newline='', encoding='utf-8') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                for edge in spamreader:
                    a = int(edge[0])
                    b = int(edge[1])
                    c = edge[2]
                    if low <= c < high:
                        if G.has_edge(a, b):
                            G.add_edge(a, b, weight=G.get_edge_data(a, b)['weight'] + 1)
                        else:
                            G.add_edge(a, b, weight=1)
                    else:
                        G.add_nodes_from([a, b])
            if len(G.nodes) > 0: analyze_func(G, ["回复关系网络", low])


class UserSimilarityNetwork:
    """
    由用户评论的相似性组建的用户相似性网络
    """

    def __init__(self, db_name):
        self.name = db_name
        self.db = DataManage(db_name)
        self.stop_words = libs.read_stop_words()

    def __handle_a_comment(self, user_to_words_count, user, text):
        text = libs.remove_links(text)
        seg_list = jieba.cut_for_search(text)  # 对每个评论的内容分词
        word_count = defaultdict(int)  # 词语到数量的映射
        for word in seg_list:
            if len(word) < 2 or word in self.stop_words: continue  # 去除过短或没用的词
            word_count[word] += 1  # 统计词语数量
        if user['id'] not in user_to_words_count:  # 本评论的用户不存在
            user_to_words_count[user['id']] = word_count  # 将用户ID映射到word_count
        else:
            for word in word_count:
                user_to_words_count[user['id']][word] += word_count[word]

    def export_to_file(self, comments=None, childes=None, title=None):
        """
        不加参数是导出静态网络关系.
        """
        user_to_words_count = defaultdict(lambda: defaultdict(int))
        if comments is None: comments = self.db.get_comments()
        for comment in comments:
            self.__handle_a_comment(user_to_words_count, comment['user'], comment['text'])
        if childes is None: childes = self.db.get_childes()
        for child in childes:
            text = child['reply_original_text'] if "reply_original_text" in child else child['text']
            self.__handle_a_comment(user_to_words_count, child['user'], text)
        for u in user_to_words_count:
            import operator
            word_counts = user_to_words_count[u]
            w = sorted(word_counts.items(), key=operator.itemgetter(1), reverse=True)
            length = min([10, len(w)])      # TODO 频率最高的10个词语
            top_words = set()
            for i in range(length):
                top_words.add(w[i][0])
            user_to_words_count[u] = top_words
        users_list = list(user_to_words_count)
        file_name = 'export/similarity_network/%s.csv' % (self.name if title is None else title)
        with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in range(len(user_to_words_count)):
                for j in range(i + 1, len(user_to_words_count)):
                    weight = len(user_to_words_count[users_list[i]].intersection(user_to_words_count[users_list[j]]))
                    if weight > 0:
                        csv_writer.writerow([users_list[i], users_list[j], weight])
        import os
        if os.path.getsize(file_name) == 0: os.remove(file_name)

    def export_to_file_with_period(self, period=1):
        """
        导出具有周期的动态关系
        :param period: 周期(天数)
        """
        comments = self.db.get_comments()
        min_date = datetime(2100, 12, 31)
        max_date = datetime(1970, 1, 1)
        for comment in comments:
            d = datetime.strptime(comment['created_at'], '%a %b %d %H:%M:%S +0800 %Y')
            if d < min_date:
                min_date = d
            elif d > max_date:
                max_date = d
        childes = self.db.get_childes()
        for child in childes:
            d = datetime.strptime(child['created_at'], '%a %b %d %H:%M:%S +0800 %Y')
            if d < min_date:
                min_date = d
            elif d > max_date:
                max_date = d
        min_date.replace(hour=0, minute=0, second=0)
        i = min_date
        while i <= max_date:
            low = i
            i += timedelta(days=period)
            high = i
            comments = self.db.get_comments()
            childes = self.db.get_childes()
            comments_in_interval = []
            childes_in_interval = []
            for comment in comments:
                d = datetime.strptime(comment['created_at'], '%a %b %d %H:%M:%S +0800 %Y')
                if low <= d < high:
                    comments_in_interval.append(comment)
            for child in childes:
                d = datetime.strptime(child['created_at'], '%a %b %d %H:%M:%S +0800 %Y')
                if low <= d < high:
                    childes_in_interval.append(child)
            if len(comments_in_interval) > 0 or len(childes_in_interval) > 0:
                print("[%s] 评论%s个 子评论%s个" % (datetime.strftime(low, "%Y-%m-%d"), len(comments_in_interval), len(childes_in_interval)))
                self.export_to_file(comments_in_interval, childes_in_interval, title="periods/%s_%s" % (self.name, datetime.strftime(low, "%Y-%m-%d")))

    def load_network(self, analyze_func=None, file_name=None):
        G = nx.Graph()
        if file_name is None: file_name = 'export/similarity_network/%s.csv' % self.name
        with open(file_name, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for edge in csv_reader:
                G.add_edge(int(edge[0]), int(edge[1]), weight=int(edge[2]))
        if analyze_func is not None:
            analyze_func(G, "用户相似性网络")
        else:
            return G

    def load_network_with_period(self, analyze_func):
        import os
        folder = 'export/similarity_network/periods'
        files = os.listdir(folder)
        for file in files:
            if file.startswith(self.name):
                G = self.load_network(None, '%s/%s' % (folder, file))
                analyze_func(G, ["用户相似性网络", file[len(self.name) + 1:-4]])


class WordsNetwork:
    """
    由单词共同出现的频率组成的单词网络
    """

    def __init__(self, db_name):
        self.name = db_name
        self.db = DataManage(db_name)
        self.stop_words = libs.read_stop_words()

    def __add_words_to_network(self, G, weibo):
        """
        分析一个微博, 将相关关系添加到图G中
        :param G: 图G
        :param weibo: 微博(复杂的dict对象)
        """
        text = weibo['longText']['longTextContent'] if weibo['isLongText'] else weibo['text']
        text = libs.remove_links(text)
        seg_list = jieba.cut_for_search(text)  # 分词成词语列表
        word_count = defaultdict(int)  # defaultdict<int>: 如果键不存在则返回0
        for word in seg_list:
            if len(word) < 2 or word in self.stop_words: continue  # 删除过短的词语和停用词
            word_count[word] += 1
        result = sorted(word_count.items(), key=lambda item: item[1], reverse=True)
        length = min(10, len(result))  # 要提取频率top 3的词语
        for i in range(length):
            G.add_node(result[i][0])  # 将词语添加到图中(NetworkX自动去重)
        for i in range(length):
            for j in range(i + 1, length):
                # 如果边存在, 权重weight+1; 如果不存在, 添加一条边,
                if G.has_edge(result[i][0], result[j][0]):
                    G.add_edge(result[i][0], result[j][0], weight=G.get_edge_data(result[i][0], result[j][0])['weight'] + 1)
                else:
                    G.add_edge(result[i][0], result[j][0], weight=1)

    def export_to_file(self):
        """
        分析微博中的词
        :return:
        """
        weibos = self.db.get_mblogs()
        G = nx.Graph()  # 无向图
        for weibo in weibos:
            self.__add_words_to_network(G, weibo)
        nx.write_adjlist(G, open("export/words_network/%s.adjlist" % self.name,'wb'))

    def export_to_file_with_period(self, period):
        """
        以period为周期建立动态的词语网络
        :param period: 周期
        """
        frequency = int(period)
        weibo_everyday = defaultdict(list)
        weibos = self.db.get_mblogs()
        # 统计每个日期有多少条微博
        for weibo in weibos:
            if len(weibo['created_at']) == 5:  # 日期格式修正(长度为5是不带年份的)
                weibo['created_at'] = "2019-" + weibo['created_at']
            weibo_everyday[weibo['created_at']].append(weibo)
        # 求出微博的最大日期和最小日期
        min_date = datetime.strptime(min(weibo_everyday), "%Y-%m-%d")
        max_date = datetime.strptime(max(weibo_everyday), "%Y-%m-%d")
        # 从最小日期开始循环, 每次日期+1天
        i = min_date
        group_time = ""
        group_seq = frequency
        weibo_every_period = defaultdict(list)
        while i <= max_date:
            time_str = i.strftime("%Y-%m-%d")  # 输出为2019-01-11这种的字符串
            if group_seq == frequency:  # 如果满一组, 进行进行相关初始化操作
                group_seq = 0
                group_time = time_str
            if time_str in weibo_everyday:
                for weibo in weibo_everyday[time_str]:
                    weibo_every_period[group_time].append(weibo)
            i = i + timedelta(days=1)
            group_seq += 1
        for c in weibo_every_period:
            G = nx.Graph()
            for weibo in weibo_every_period[c]:
                self.__add_words_to_network(G, weibo)
            nx.write_adjlist(G, "export/words_network/periods/%s_%s.adjlist" % (self.name, c))

    def load_network(self, analyze_func):
        G = nx.read_adjlist("words_network.adjlist")
        analyze_func(G, "词语网络")

    def load_network_with_period(self, analyze_func):
        import os
        files = os.listdir('.')
        for file in files:
            if file.startswith("words_network.20"):
                G = nx.read_adjlist(file)
                analyze_func(G, ["词语网络", file[len("words_network."):-8]])


class RepostNetwork:
    """
    转发关系网络
    """

    def __init__(self, db_name):
        self.name = db_name
        self.db = DataManage(db_name)

    @staticmethod
    def find_repost_member(text):
        import re
        if text in ('转发微博', '轉發微博', '转发', 'Repost'): return None
        regex = r"[^/]*?//<a.*?href=['\"]/n/(.*?)['\"].*?>@.*?</a>"
        result = re.findall(regex, text)
        if len(result) > 0 and len(result[0]) > 0: return result[0]

    def export_to_file(self):
        with open('export/repost_network/edges_%s.csv' % self.name, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            reposts = self.db.get_reposts()
            for repost in reposts:
                try:
                    date = ('2019-' + repost['created_at']) if len(repost['created_at']) == 5 else repost['created_at']
                    result = RepostNetwork.find_repost_member(repost['text'])
                    if result is None: result = repost['retweeted_status']['user']['screen_name']
                    csv_writer.writerow([repost['user']['screen_name'], result, date])
                except TypeError:
                    print(repost)

    def load_network(self, analyze_func):
        G = nx.DiGraph()
        with open('export/repost_network/edges_%s.csv' % self.name, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for edge in csv_reader:
                a = edge[0]
                b = edge[1]
                if G.has_edge(a, b):
                    G.add_edge(a, b, weight=G.get_edge_data(a, b)['weight'] + 1)
                else:
                    G.add_edge(a, b, weight=1)
        analyze_func(G, "转发关系网络")

    def load_network_with_period(self, analyze_func, period=1):
        min_date_str = '9999-99-99'
        max_date_str = '0000-00-00'
        with open('export/repost_network/edges_%s.csv' % self.name, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for edge in csv_reader:
                d = edge[2]
                if d < min_date_str:
                    min_date_str = d
                elif d > max_date_str:
                    max_date_str = d
        min_date = datetime.strptime(min_date_str, "%Y-%m-%d")
        max_date = datetime.strptime(max_date_str, "%Y-%m-%d")
        i = min_date
        while i <= max_date:
            low = i.strftime("%Y-%m-%d")  # 输出为2019-01-11这种的字符串
            i = i + timedelta(days=period)
            high = i.strftime("%Y-%m-%d")
            G = nx.DiGraph()
            with open('export/repost_network/edges_%s.csv' % self.name, 'r', newline='', encoding='utf-8') as csvfile:
                csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                for edge in csv_reader:
                    a = edge[0]
                    b = edge[1]
                    c = edge[2]
                    if low <= c < high:  # 竟然能连续比较!!
                        if G.has_edge(a, b):
                            G.add_edge(a, b, weight=G.get_edge_data(a, b)['weight'] + 1)
                        else:
                            G.add_edge(a, b, weight=1)
                    else:
                        G.add_nodes_from([a, b])
                if len(G.nodes) > 0: analyze_func(G, ("转发关系网络", low))


class NetworkExportToTableau:

    @staticmethod
    def export_graph_degrees(G):
        pass

    @staticmethod
    def export_di_graph_degree(G):
        pass

def execute(name):
    from analyzer1 import NetworkAnalyzer as NetworkAnalyzer

    db_name = libs.to_db_name(name)
    # 关系导出
    reply = ReplyNetwork(db_name)
    reply.export_to_file()
    repost = RepostNetwork(db_name)
    repost.export_to_file()
    us = UserSimilarityNetwork(db_name)
    us.export_to_file()
    us.export_to_file_with_period(period=1)
    wn = WordsNetwork(db_name)
    wn.export_to_file()
    wn.export_to_file_with_period(period=1)
    # 静态网络加载与分析 (示例)
    a = NetworkAnalyzer()
    reply.load_network(a.degree_distribution)
    repost.load_network(a.degree_distribution)
    us.load_network(a.degree_distribution)
    wn.load_network(a.degree_distribution)
    a.plot_degree_distribution()
    # 动态网络加载与分析 (示例)
    from analyzer2 import NetworkAnalyzer as NetworkAnalyzer
    a = NetworkAnalyzer()
    reply.load_network_with_period(a.dynamic_analyze, period=1)
    repost.load_network_with_period(a.dynamic_analyze, period=1)
    us.load_network_with_period(a.dynamic_analyze)
    wn.load_network_with_period(a.dynamic_analyze)
    a.save_result()

if __name__ == '__main__':
    # dbname = "weibo"
    # dbname = 'zhuwen'
    execute('基因编辑婴儿')
    #############测试区域#############
    # from analyzer2 import NetworkAnalyzer as NetworkAnalyzer
    # a = NetworkAnalyzer()
    # a.plot_clustering_coefficients()
    # p = RepostNetwork(dbname)
    # p.load_network_with_period(a.max_community_analyze, period=1)
    # r = ReplyNetwork(dbname)
    # r.load_network_with_period(a.max_community_analyze, period=1)
    #################################
    # p = RepostNetwork(dbname)
    # p.load_network_with_period(a.dynamic_spring, period=1)
    # r = ReplyNetwork(dbname)
    # r.load_network_with_period(a.dynamic_spring, period=1)
    # w = WordsNetwork(dbname)
    # w.load_network_with_period(a.dynamic_spring)
    # u = UserSimilarityNetwork(dbname)
    # u.load_network_with_period(a.dynamic_spring)
    # a.save_result("basic.csv")
    ################################
    # p = RepostNetwork(dbname)
    # p.load_network(a.degree_distribution)
    # r = ReplyNetwork(dbname)
    # r.load_network(a.degree_distribution)
    # w = WordsNetwork(dbname)
    # w.load_network(a.degree_distribution)
    # u = UserSimilarityNetwork(dbname)
    # u.load_network(a.degree_distribution)
    # a.plot_degree_distribution()
