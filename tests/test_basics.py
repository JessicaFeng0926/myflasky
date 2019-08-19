import unittest
from flask import current_app
from app import create_app,db

class BasicsTestCase(unittest.TestCase):
    '''这是一个单元测试'''
    def setUp(self):
        #使用测试环境创建程序并激活程序上下文
        self.app=create_app('testing')
        self.app_context=self.app.app_context()
        self.app_context.push()
        #创建用于测试的数据表
        db.create_all()

    def tearDown(self):
        #删除用于测试的数据表
        db.session.remove()
        db.drop_all()
        #删除活动的程序
        self.app_context.pop()

    def test_app_exists(self):
        '''这个测试证明当前app确实存在'''
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        '''这个测试证明当前配置确实是用于测试的配置'''
        self.assertTrue(current_app.config['TESTING'])


