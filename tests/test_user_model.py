import unittest
from app.models import User,Role,Permission,AnonymousUser
from app import db,create_app

class UserModelTestCase(unittest.TestCase):
    '''这是用户模型的单元测试'''
    def setUp(self):
        #使用测试环境创建程序并激活程序上下文
        self.app=create_app('testing')
        self.app_context=self.app.app_context()
        self.app_context.push()
        #创建用于测试的数据表
        db.create_all()
        #想数据表中插入角色数据
        Role.insert_roles()

    def tearDown(self):
        #删除用于测试的数据表
        db.session.remove()
        db.drop_all()
        #删除活动的程序
        self.app_context.pop()
    def test_password_setter(self):
        '''这是测试密码哈希值的设置功能的'''
        u=User(password='cat')
        #断言用户实例u的密码散列值不为空
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        '''这是测试密码确实不可读'''
        u=User(password='cat')
        #只要试图读取password，就会抛出属性错误异常
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        '''这是测试验证密码的方法是否可靠'''
        u=User(password='cat')
        #断言输入的密码和设置的密码一致时验证方法就能返回True
        self.assertTrue(u.verify_password('cat'))
        #断言输入的密码和设置的密码不一致时验证方法就会返回False
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        '''这个测试验证散列值是随机的'''
        u=User(password='cat')
        u2=User(password='cat')
        #断言即使两个用户的密码一样，密码的散列值也不相同
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_generate_confirmation_token(self):
        '''这个测试验证确实能够生成一个token'''
        u=User(username='test')
        db.session.add(u)
        u=User.query.filter_by(username='test').first()
        self.assertTrue(u.generate_confirmation_token() is not None)

    def test_confirm(self):
        '''这个测试验证用户类的confirm方法能针对不同情况作出正确的反应'''
        u=User(username='test1')
        u2=User(username='test2')
        db.session.add(u)
        db.session.add(u2)
        u=User.query.filter_by(username='test1').first()
        u2=User.query.filter_by(username='test2').first()
        token=u.generate_confirmation_token()
        self.assertFalse(u.confirm('a wrong token'))
        self.assertFalse(u2.confirm(token))
        self.assertTrue(u.confirm(token))

    def test_roles_and_permissions(self):
        '''这是测试普通用户的权限是否正确'''
        u=User(email='jessica@example.com',password='dog')
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

    def test_anonymous_user(self):
        '''这是测试匿名用户的权限'''
        u=AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))

    



    