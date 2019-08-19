from selenium import webdriver
import unittest
from app import create_app,db
from app.models import Role,User,Post,Comment
import threading
import time

class SeleniumTestCase(unittest.TestCase):
    '''这是自动化测试'''
    client=None

    @classmethod
    def setUpClass(cls):
        '''这是一个创建浏览器引擎的类方法'''
        #启动浏览器
        options=webdriver.ChromeOptions()
        #加了这个参数，就是让浏览器默默运行，而不会弹出一个真实的浏览器窗口
        options.add_argument('headless')
        try:
            cls.client=webdriver.Chrome(executable_path=r'C:\Users\22768\AppData\Local\Google\Chrome\Application\chromedriver.exe',chrome_options=options)
        except:
            pass

        #只有在能够启动浏览器的情况下，才执行下面的代码
        if cls.client:
            #创建并激活程序
            cls.app=create_app('testing')
            cls.app_context=cls.app.app_context()
            cls.app_context.push()

            #禁止日志，保持输出简洁
            import logging
            logger=logging.getLogger('werkzeug')
            logger.setLevel('ERROR')

            #创建数据库，并插入一些用于测试的虚拟数据
            db.create_all()
            Role.insert_roles()
            User.generate_fake(10)
            Post.generate_fake(10)

            #添加管理员
            admin_role=Role.query.filter_by(permissions=0xff).first()
            admin=User(email='john1@example.com',username='john1',
                    password='cat',confirmed=True,role=admin_role)
            db.session.add(admin)
            db.session.commit()

            #在一个线程中启动服务器
            cls.server_thread=threading.Thread(target=cls.app.run)
            cls.server_thread.start()

            #给它一秒钟的时间，确保服务器已经启动
            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        '''这是一个静态方法，用于在测试完成后做一些善后工作'''
        #只有在浏览器正常启动的情况下才执行下面的操作
        if cls.client:
            #关闭服务器和浏览器
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join()

            #销毁数据库
            db.session.remove()
            db.drop_all()

            #删除程序上下文
            cls.app_context.pop()

    def setUp(self):
        '''这是测试之前执行的一个实例方法'''
        if not self.client:
            #如果浏览器没有启动，就跳过测试，并且给出原因
            self.skipTest('浏览器没有启动')

    def tearDown(self):
        '''这是此时之后执行的一个实例方法，这里就略过了'''
        pass

    def test_admin_home_page(self):
        '''这是以管理员身份访问主页的测试'''
        #进入主页，还没有登录
        self.client.get('http://localhost:5000/')
        self.assertTrue('您好，陌生人' in self.client.page_source)

        #进入登录页面
        self.client.find_element_by_link_text('登录').click()
        self.assertTrue('<h1>登录</h1>' in self.client.page_source)

        #登录
        self.client.find_element_by_name('email').send_keys('john1@example.com')
        self.client.find_element_by_name('password').send_keys('cat')
        self.client.find_element_by_name('submit').click()
        self.assertTrue('您好，john1' in self.client.page_source)

        #进入用户个人资料面
        self.client.find_element_by_link_text('个人资料').click()
        self.assertTrue('<h1>john1</h1>' in self.client.page_source)







