import unittest
from app import create_app,db
from app.models import User,Role
from flask import url_for


class FlaskClientTestCase(unittest.TestCase):
    '''这是使用Flask客户端编写的测试'''
    def setUp(self):
        '''这是每次测试之前必须执行的准备工作'''
        #创建程序
        self.app=create_app('testing')
        #激活程序上下文
        self.app_context=self.app.app_context()
        self.app_context.push()
        #创建数据表
        db.create_all()
        #插入用户角色
        Role.insert_roles()
        #创建测试客户端
        self.client=self.app.test_client(use_cookies=True)
    
    def tearDown(self):
        '''这是测试结束需要执行的一些收尾工作'''
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        '''这是对主页的测试'''
        response=self.client.get(url_for('main.index'))
        self.assertTrue('陌生人' in response.get_data(as_text=True))
    
    def test_register_and_login(self):
        '''这是测试注册、登录、确认账号和退出功能'''
        #先检查注册
        response=self.client.post(url_for('auth.register'),data={
            'email':'json@example.com',
            'username':'json',
            'password':'cat',
            'password2':'cat',
        })
        self.assertTrue(response.status_code==302)
        #再检查登录
        response=self.client.post(url_for('auth.login'),data={
            'email':'json@example.com',
            'password':'cat'
        },follow_redirects=True)
        data=response.get_data(as_text=True)
        self.assertTrue('您好，json' in data)
        self.assertTrue('您还没有确认您的账号' in data)

        #发送确认令牌
        user=User.query.filter_by(email='json@example.com').first()
        token=user.generate_confirmation_token()
        response=self.client.get(url_for('auth.confirm',token=token),follow_redirects=True)
        data=response.get_data(as_text=True)
        self.assertTrue('您的账号已经成功确认' in data)

        #退出
        response=self.client.get(url_for('auth.logout'),follow_redirects=True)
        data=response.get_data(as_text=True)
        self.assertTrue('您已退出登录' in data)





        


