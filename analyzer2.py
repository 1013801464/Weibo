from collections import defaultdict

import networkx as nx
import numpy as np


class NetworkAnalyzer:
    def __init__(self):
        self.result = []

    def average_closeness_centrality(self, G, name):
        """
        紧密度中心性 (用最大连通子图求的)
        :param G: 图
        :param name: 图名
        :return: 不返回
        """
        print("正在计算%s的紧密度中心性..." % name)
        degrees = defaultdict(int)
        avg_closeness_centrality = defaultdict(int)
        if type(G) == nx.DiGraph: G = G.to_undirected(reciprocal=False)  # 转为无向图
        G = G.subgraph(max(nx.connected_components(G), key=len))  # 最大连通子图
        closeness_centrality = nx.closeness_centrality(G)
        for node in G.nodes:
            d = G.degree[node]
            degrees[d] += 1
            avg_closeness_centrality[d] += closeness_centrality[node]
        for d in avg_closeness_centrality:
            avg_closeness_centrality[d] /= degrees[d]
        np.save(name + ".closeness.npy", np.array(sorted(avg_closeness_centrality.items())))
        print("完成")

    def plot_average_closeness_centrality(self, names=('转发关系网络', '回复关系网络', '词语网络', '用户相似性网络')):
        print("正在绘制紧密度中心性...", end="")
        import matplotlib.pyplot as plt
        closeness_centrality = {}
        for name in names:
            closeness_centrality[name] = np.load(name + ".closeness.npy")
        colors = iter(['r+', 'g*', 'b.', 'y.', 'c+', 'm*'])
        for c in closeness_centrality:
            plt.semilogx(closeness_centrality[c][..., 0], closeness_centrality[c][..., 1] / np.sum(closeness_centrality[c][..., 1]), next(colors), label=c)
        plt.xlabel('Degree (k)')
        plt.ylabel('<C|k>')
        plt.legend(loc=0)
        plt.show()
        print("完成")

    def average_neighbor_degree(self, G, name):
        """
        分析图G的平均邻度 (在最大连通子图上求)
        :param G:
        :param name:
        :return:
        """
        if type(G) == nx.DiGraph:  # 有向图要求最大连通子图 + 权重要求和
            G = G.subgraph(max(nx.weakly_connected_components(G), key=len))  # 求弱连通子图
            G1 = G.to_undirected(reciprocal=False)  # 存在一条边即可
            G2 = G.to_undirected(reciprocal=True)  # 只有相互转发才会保存
            for edge in G2.edges:
                if edge[0] != edge[1]:
                    G1.add_edge(edge[0], edge[1], weight=G.get_edge_data(edge[0], edge[1])['weight'] + G.get_edge_data(edge[1], edge[0])['weight'])
            G = G1
        else:  # 无向图直接求最大连通子图
            G = G.subgraph(max(nx.connected_components(G), key=len))  # 最大连通子图
        print("%s: 节点个数%s 边个数%s" % (name, len(G.nodes), len(G.edges)))
        degrees = defaultdict(int)  # 某个度的出现次数
        avg_avg_neighbor_degree = defaultdict(int)
        avg_avg_weighted_neighbor_degree = defaultdict(float)
        avg_neighbor_degree = nx.average_neighbor_degree(G)
        avg_weighted_neighbor_degree = nx.average_neighbor_degree(G, weight="weight")
        for node in G.nodes:
            d = G.degree[node]
            degrees[d] += 1
            avg_avg_neighbor_degree[d] += avg_neighbor_degree[node]
            avg_avg_weighted_neighbor_degree[d] += avg_weighted_neighbor_degree[node]
        for d in degrees:
            avg_avg_neighbor_degree[d] /= degrees[d]
            avg_avg_weighted_neighbor_degree[d] /= degrees[d]
        np.save(name + ".neighbor_degree.npy", np.array(sorted(avg_avg_neighbor_degree.items())))
        np.save(name + ".weighted_neighbor_degree.npy", np.array(sorted(avg_avg_weighted_neighbor_degree.items())))

    def plot_average_neighbor_degree(self, names=('回复关系网络', '词语网络', '用户相似性网络', '转发关系网络')):
        print("正在绘制平均邻度...", end="")
        import matplotlib.pyplot as plt
        colors = iter(['rx', 'g+', 'b.', 'y*', 'r.', 'g.', 'b.', 'y.'])
        average_neighbor_degree = {}
        for name in names:
            average_neighbor_degree[name] = np.load(name + ".neighbor_degree.npy")
        for c in average_neighbor_degree:
            plt.loglog(average_neighbor_degree[c][..., 0], average_neighbor_degree[c][..., 1], next(colors), label=c)
        plt.legend(loc=0)
        plt.xlabel("degree (k)")
        plt.ylabel("$<k_{nn}|k>$")
        plt.show()
        plt.close()
        #### 另一个
        colors = iter(['rx', 'g+', 'b.', 'y*', 'r.', 'g.', 'b.', 'y.'])
        average_neighbor_degree = {}
        for name in names:
            average_neighbor_degree[name] = np.load(name + ".weighted_neighbor_degree.npy")
        for c in average_neighbor_degree:
            plt.loglog(average_neighbor_degree[c][..., 0], average_neighbor_degree[c][..., 1], next(colors), label=c)
        plt.legend(loc=0)
        plt.xlabel("degree (k)")
        plt.ylabel("$<k_{nn}^w|k>$")
        plt.show()

    def clustering_coefficients(self, G, name):
        """
        聚类系数分析
        有向图: 在弱连通子图上做
        无向图: 在连通子图上做
        :param G:
        """
        print("正在计算 %s 的聚类系数..." % name)
        degrees = defaultdict(int)  # 每个度有多少个
        if type(G) == nx.DiGraph:
            G = G.subgraph(max(nx.weakly_connected_components(G), key=len))  # 求最大弱连通子图
            G1 = G.to_undirected(reciprocal=False)  # 存在一条边即可
            G2 = G.to_undirected(reciprocal=True)  # 只有相互转发才会保存
            for edge in G2.edges:
                if edge[0] != edge[1]:
                    G1.add_edge(edge[0], edge[1], weight=G.get_edge_data(edge[0], edge[1])['weight'] + G.get_edge_data(edge[1], edge[0])['weight'])
            G = G1
        else:
            G = G.subgraph(max(nx.connected_components(G), key=len))
        cs = nx.clustering(G)  # 存储每个节点的聚类系数(这个过程较慢)
        weighted_cs = nx.clustering(G, weight="weight")  # 存储每个节点的聚类系数(这个过程较慢)
        coefficients = defaultdict(int)  # 每个度的系数之和
        weighted_coefficients = defaultdict(int)  # 每个度的系数之和
        for node in G.nodes:
            d = G.degree[node]
            degrees[d] += 1
            coefficients[d] += cs[node]
            weighted_coefficients[d] += weighted_cs[node]
        for d in degrees:
            coefficients[d] /= degrees[d]
            weighted_coefficients[d] /= degrees[d]
        np.save(name + ".clustering.npy", np.array(sorted(coefficients.items())))
        np.save(name + ".weighted_clustering.npy", np.array(sorted(weighted_coefficients.items())))

    def plot_clustering_coefficients(self, names=('转发关系网络', '回复关系网络', '词语网络')):
        print("正在绘制聚类系数...", end="")
        import matplotlib.pyplot as plt
        colors = iter(['r+', 'g*', 'b.', 'yx', 'c+', 'm*'])
        clustering = {}
        for name in names:
            clustering[name] = np.load(name + ".clustering.npy")
        for c in clustering:
            plt.loglog(clustering[c][..., 0], clustering[c][..., 1], next(colors), label=c)
        plt.legend(loc=0)  # 添加图例, 图例位置自动
        plt.xlabel("degree (k)")
        plt.ylabel("<C|k>")
        plt.show()
        plt.close()
        colors = iter(['r+', 'g*', 'b.', 'yx', 'c+', 'm*'])
        weighted_clustering = {}
        for name in names:
            weighted_clustering[name] = np.load(name + ".weighted_clustering.npy")
        for c in weighted_clustering:
            plt.loglog(weighted_clustering[c][..., 0], weighted_clustering[c][..., 1], next(colors), label=c)
        plt.legend(loc=0)  # 添加图例, 图例位置自动
        plt.xlabel("degree (k)")
        plt.ylabel("$<C_w|k>$")
        plt.show()
        print("完成")

    def average_shortest_path_length(self, G, name):
        if type(G) == nx.DiGraph:  # 有向图要求最大连通子图 + 权重要求和
            G = G.subgraph(max(nx.weakly_connected_components(G), key=len))  # 求弱连通子图
            G1 = G.to_undirected(reciprocal=False)  # 存在一条边即可
            G2 = G.to_undirected(reciprocal=True)  # 只有相互转发才会保存
            for edge in G2.edges:
                if edge[0] != edge[1]:
                    G1.add_edge(edge[0], edge[1], weight=G.get_edge_data(edge[0], edge[1])['weight'] + G.get_edge_data(edge[1], edge[0])['weight'])
            G = G1
        else:  # 无向图直接求最大连通子图
            G = G.subgraph(max(nx.connected_components(G), key=len))  # 最大连通子图
        print("%s : %s" % (name, nx.average_shortest_path_length(G)))

    def dynamic_analyze(self, G, name):
        print("正在计算 %s %s ..." % (name[0], name[1]))
        s = 0
        for d in G.degree:
            s += d[1]
        l = len(G.degree)
        r1 = (s / l)
        print('平均度 %s' % r1)
        # 求最短路径长度 (已经按照无向图 + 最大连通子图处理)
        if type(G) == nx.DiGraph: G = G.to_undirected(reciprocal=False)
        G = G.subgraph(max(nx.connected_components(G), key=len))
        if name[0].find("转发") == -1 and name[0].find("回复") == -1 and name[0].find("用户相似性") == -1:
            r2 = nx.average_shortest_path_length(G)
            print('平均路径长度 %s' % r2)
        else:
            r2 = None
        if name[0].find("用户相似性") == -1:
            r3 = nx.average_clustering(G)
            print("平均聚类系数 %s" % r3)
        else:
            r3 = None
        self.result.append([name[0], name[1], r1, r2, r3])

    def save_result(self, file="result.csv"):
        import csv
        with open(file, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for item in self.result:
                csv_writer.writerow(item)

    def dynamic_nodes_and_edges(self, G, name):
        print("正在计算 %s %s ..." % (name[0], name[1]))
        nodes = len(G.nodes)
        edges = len(G.edges)
        if type(G) == nx.DiGraph: G = G.to_undirected(reciprocal=False)
        G = G.subgraph(max(nx.connected_components(G), key=len))
        com_nodes = len(G.nodes)
        com_edges = len(G.edges)
        self.result.append([name[0], name[1], nodes, edges, com_nodes, com_edges])

    def dynamic_spring(self, G, name):
        import json
        import networkx as nx
        print(name)
        if type(G) == nx.DiGraph:
            G = G.to_undirected(reciprocal=False)
        print(max(G.nodes, key=lambda x:G.degree(x)))
        with open('community/spring_layout.%s_%s.json' % (name[0], name[1]), 'w') as f:
            json.dump(nx.spring_layout(G, k=0.02), f)

