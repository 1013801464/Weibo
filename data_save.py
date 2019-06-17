from pymongo import MongoClient


class Test:
    def __init__(self):
        self.weibo = None
        self.zhuwen = None
        self.monkey = None


m = MongoClient("localhost", 27017)  # 保持单例状态


# m = Test()

class DataManage:
    def __init__(self, db_name):
         # print("正在打开数据库" + db_name)
         self.db = m.get_database(db_name)

    def get_mblogs(self):
        '''
        获得所有的微博
        :return:
        '''
        return self.db.blogs.find()

    def get_a_blog(self, blog_id):
        '''
        获得指定id的微博
        :param blog_id:
        :return:
        '''
        return self.db.blogs.find_one({'id': blog_id})

    def get_comments(self):
        '''
        获得所有的评论
        :return:
        '''
        return self.db.comments.find()

    def get_reposts(self):
        """
        获得所有转发
        :return:
        """
        return self.db.reposts.find()

    def get_reposts_of_users(self, screen_name):
        """
        获得某个用户的所有转发
        :param screen_name: 用户的显示名称
        :return:
        """
        return self.db.reposts.find({"user.screen_name": screen_name})

    def get_reposts_of_root(self, id):
        return self.db.reposts.find({"retweeted_status.id": id})

    def get_comments_of_root(self, id):
        """
        获得父节点为ID的所有评论
        :param id:
        :return:
        """
        return self.db.comments.find({"rootid": id})

    def get_childes_of_root(self, id):
        """
        获得父节点为ID的所有子评论
        :param id:
        :return:
        """
        return self.db.childs.find({"rootid": id})

    def get_comments_of_users(self, user_id):
        """
        返回某个用户ID的所有评论
        :param user_id:
        :return:
        """
        return self.db.comments.find({"user.id": user_id})

    def get_childes_of_users(self, user_id):
        """
        返回某个用户ID的所有子评论
        :param user_id:
        :return:
        """
        return self.db.childs.find({"user.id": user_id})

    def get_childes(self):
        '''
        获得所有评论的评论
        :return:
        '''
        return self.db.childs.find()

    def get_users(self):
        '''
        获得users表中的数据
        :return:
        '''
        return self.db.users.find()

    def get_user_name(self, user_id):
        '''
        根据用户ID获取用户昵称
        :return:
        '''
        return self.db.users.find_one({"id": user_id})['screen_name']

    def save_mblog(self, mblog):
        '''
        保存微博
        :param mblog:
        :return:
        '''
        self.db.blogs.replace_one({"id": mblog["id"]}, mblog, True)
        print(mblog['created_at'], end='')
        print(mblog['text'])

    def save_comment(self, comment):
        '''
        保存评论
        :param comment:
        :return:
        '''
        self.db.comments.replace_one({"id": comment['id']}, comment, True)

    def save_child_comment(self, child):
        '''
        保存评论的评论
        :param child:
        :return:
        '''
        self.db.childs.replace_one({"id": child['id']}, child, True)

    def save_user(self, user):
        '''
        保存(从数据库中抽取的)用户
        :param user:
        :return:
        '''
        self.db.users.replace_one({"id": user['id']}, user, True)


    def save_repost(self, repost):
        self.db.reposts.replace_one({"id": repost["id"]}, repost, True)
        print(repost)

# test
if __name__ == '__main__':
    a = DataManage("weibo")
    print(a.get_user_name(5759325134))
