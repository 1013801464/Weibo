from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


class NetworkAnalyzer:
    def __init__(self):
        self.degree_distributions = dict()
        self.weighted_clustering = dict()
        self.components_sizes = dict()
        self.clustering = dict()
        self.neighbor_degree = dict()
        self.weighted_neighor_degree = dict()
        self.closeness_centrality = dict()

    def count_nodes_and_edges(self, G, name):
        print("统计 %s 节点%s个 边%s个" % (name, len(G.nodes), len(G.edges)))
        if type(G) == nx.DiGraph:
            largest_cc = max(nx.weakly_connected_components(G), key=len)
        else:
            largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc)
        print("最大连通子图 %s 节点%s个 边%s个" % (name, len(G.nodes), len(G.edges)))
        print("")

    def components_distribution(self, G, name):
        """
        孤立连通子图的大小分布
        :param G: 图
        :param name: 图的名字
        """
        if type(G) == nx.DiGraph: G = G.to_undirected(reciprocal=False)
        sizes = [len(c) for c in sorted(nx.connected_components(G), key=len, reverse=True)]
        size_count = defaultdict(int)
        for i in sizes:
            size_count[i] += 1
        self.components_sizes[name] = np.array(sorted(size_count.items()))

    def plot_components_distribution(self):
        from scipy.optimize import curve_fit

        def fit_func(x, a):
            return x ** -(1 + a)

        print("正在绘制连通子图的分布...", end="")
        colors = iter(['r+', 'g*', 'b.', 'y.', 'c+', 'm*'])
        for c in self.components_sizes:
            plt.loglog(self.components_sizes[c][..., 0], self.components_sizes[c][..., 1] / np.sum(self.components_sizes[c][..., 1]), next(colors), label=c)
            if c.find("转发") != -1 or c.find("回复") != -1:
                popt, pcov = curve_fit(fit_func, self.components_sizes[c][..., 0], self.components_sizes[c][..., 1] / np.sum(self.components_sizes[c][..., 1]))
                print(popt)
        plt.xlabel('Component Size (s)')
        plt.ylabel('p(s)')
        plt.legend(loc=0)
        plt.show()
        print("完成")

    # def connectivity(self, G, name):
    #     from networkx.algorithms import approximation
    #     approximation.all_pairs_node_connectivity(G)
    #     approximation.node_connectivity(G)
    #     approximation.k_components(G)
    #     approximation.max_clique(G)
    #     approximation.large_clique_size(G)
    #     return "同类性: %s" % nx.degree_assortativity_coefficient(G)

    def degree_distribution(self, G, name):
        degree_distribute = defaultdict(int)
        for node in G.nodes:
            degree_distribute[G.degree[node]] += 1
        self.degree_distributions[name] = np.array(sorted(degree_distribute.items()))

    def plot_degree_distribution(self):
        colors = iter(['r+', 'g*', 'b.', 'y.', 'c+', 'm*'])
        for c in self.degree_distributions:
            plt.loglog(self.degree_distributions[c][..., 0], self.degree_distributions[c][..., 1] / np.sum(self.degree_distributions[c][..., 1]), next(colors), label=c)
        plt.legend(loc=0)
        plt.xlabel("degree (k)")
        plt.ylabel("p(k)")
        plt.show()

    def assortativity(self, G, name):
        """
        同质性
        :param G: 图
        :param name: 图名
        :return: 不返回
        """
        print("%s %s" % (name, nx.degree_assortativity_coefficient(G)))

    def k_core_number(self, G, name):
        # networkx.exception.NetworkXError: Frozen graph can't be modified
        print("计算 %s 的K内核" % name)
        if type(G) == nx.DiGraph:
            G = G.to_undirected(reciprocal=False)
        largest_cc = max(nx.connected_components(G), key=len)  # 求最大连通子图 1
        G.remove_edges_from(nx.selfloop_edges(G))
        G2 = G.subgraph(largest_cc)  # 求最大连通子图 2
        G3 = nx.algorithms.core.k_core(G2)  # 求G2的K内核
        core_dict = nx.algorithms.core.core_number(G2)  # 求所有节点对应的k值
        # 结果是回复网络是剥开3层, 转发网络是5层
        for node in G3.nodes:
            print("%s : %s" % (node, core_dict[node]))  # 输出G3的所有节点

    def community_detection(self, G, name):
        """
        进行社团检测
        :param G: 图(有向图会被转换为无向图)
        :param name: 图名
        """
        print(name)
        if type(G) == nx.DiGraph:
            G = G.to_undirected(reciprocal=False)
        from networkx.algorithms import community
        nodes_sets = community.label_propagation.label_propagation_communities(G)
        i = 0
        nodes_colors = []
        node_color_map = defaultdict(lambda: "lightgray")

        colors2 = iter(['black', 'dimgray', 'lightcoral', 'brown', 'firebrick',
                        'red', 'mistyrose', 'tomato', 'darksalmon', 'sienna',
                        'chocolate', 'saddlebrown', 'sandybrown', 'peru', 'linen',
                        'bisque', 'darkorange', 'burlywood', 'moccasin', 'wheat',
                        'darkgoldenrod', 'goldenrod', 'gold', 'khaki', 'darkkhaki',
                        'olive', 'yellow', 'olivedrab', 'darkseagreen', 'palegreen',
                        'limegreen', 'green', 'lime', 'aquamarine', 'turquoise',
                        'lightcyan', 'darkslategray', 'cyan', 'steelblue', 'dodgerblue',
                        'slategray', 'cornflowerblue', 'navy', 'blue', 'slateblue',
                        'darkslateblue', 'blueviolet', 'darkviolet', 'violet', 'fuchsia'])

        for nodes_set in nodes_sets:
            i += 1
            if len(nodes_set) > 10:
                from matplotlib import colors
                c = colors.cnames[next(colors2)]
                print("%s len=%s color=%s" % (i, len(nodes_set), c))
                for node in nodes_set:
                    node_color_map[node] = c
        for node in G.nodes:
            nodes_colors.append(node_color_map[node])
        plt.figure(figsize=(12, 12))
        print("正在计算布局", end="")
        pos = nx.spring_layout(G, k=0.02)
        print("结束")
        nx.draw_networkx_nodes(G, pos, node_size=3, node_color=nodes_colors)
        nx.draw_networkx_edges(G, pos, width=1, edge_color='#A0CBE2')
        plt.axis('off')
        plt.show()

    @staticmethod
    def get_time_str():
        return datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')

    def max_community_analyze(self, G, name):
        print(name)
        d2 = name[1]
        name = name[0]
        if d2 != '2018-11-26': return
        import jieba
        if type(G) == nx.DiGraph:
            G = G.to_undirected(reciprocal=False)
        from networkx.algorithms import community
        nodes_sets = community.label_propagation.label_propagation_communities(G)
        import heapq
        max_sets = heapq.nlargest(3, nodes_sets, key=len)
        for max_set in max_sets:
            user = max(max_set, key=lambda x: G.degree(x))
            print("%s  %s" % (user, len(max_set)))
            word_count = defaultdict(int)  # 词语到数量的映射
            from data_save import DataManage
            d = DataManage("weibo")
            # for user in max_set:
            import export_to_tableau
            if name.find("转发") != -1:
                for repost in d.get_reposts_of_root('4310753689691011'):        ## TODO 处理这个人!
                    text = export_to_tableau.clean_repost_text(repost['raw_text'])
                    if len(text) > 0:
                        word_list = jieba.cut_for_search(text)
                        for word in word_list:
                            word_count[word] += 1
            elif name.find("回复") != -1:
                for comment in d.get_comments_of_root("4310688438133188"):
                    text = comment['text']
                    if len(text) > 0:
                        word_list = jieba.cut_for_search(text)
                        for word in word_list:
                            word_count[word] += 1
                    for child in d.get_childes_of_users(comment["id"]):
                        text = child['text'] if 'reply_original_text' not in child else child['reply_original_text']
                        if len(text) > 0:
                            word_list = jieba.cut_for_search(text)
                            for word in word_list:
                                word_count[word] += 1
            import operator
            w = sorted(word_count.items(), key=operator.itemgetter(1), reverse=True)
            np.save("大社团词语_%s_%s_%s.npy" % (name, d2, len(max_set)), np.array(w))
