import unittest
import json
import re
from base64 import b64encode
from app import create_app,db
from app.models import User,Role,Post,Comment

class APITestCase(unittest.TestCase):
    '''这是对web服务的测试'''
    def setUp(self):
        '''这是每次测试之前都要做的准备工作'''
        #创建程序并激活程序上下文
        self.app=create_app('testing')
        self.app_context=self.app.app_context()
        self.app_context.push()
        #创建数据表
        db.create_all()
        #插入角色
        Role.insert_roles()
        #创建用于测试的客户端
        self.client=self.app.test_client()

    def tearDown(self):
        '''这是测试结束后的收尾工作'''  
        #清空数据库      
        db.session.remove()
        db.drop_all()
        #弹出程序上下文
        self.app_context.pop()

    def get_api_headers(self,username,password):
        '''这是获取web服务的头信息'''
        return {
            'Authorization':'Basic '+b64encode((username+':'+password).encode('utf-8')).decode('utf-8'),
            'Accept':'application/json',
            'Content-Type':'application/json',
        }

    def test_404(self):
        '''这是对404错误的测试'''
        response=self.client.get('/wrong/url',headers=self.get_api_headers('email','password'))
        self.assertEqual(response.status_code,404)
        json_response=json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['error'],'not found')

    def test_no_auth(self):
        '''这是没有通过验证的测试'''
        response=self.client.get('/api/v1.0/posts/',content_type='application/json')
        self.assertEqual(response.status_code,401)

    def test_bad_auth(self):
        '''这是验证密码错误的测试'''
        #添加一个新用户
        r=Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u=User(email='json@example.com',password='cat',confirmed=True,role=r)
        db.session.add(u)
        db.session.commit()

        #用错误的密码登录
        response=self.client.get('/api/v1.0/posts/',headers=self.get_api_headers('json@example.com','dog'))
        self.assertEqual(response.status_code,401)

    def test_token_auth(self):
        '''这是对用加密令牌的方式登录测试'''
        #创建一个用户
        r=Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u=User(email='json1@example.com',password='cat',confirmed=True,role=r)
        db.session.add(u)
        db.session.commit()

        #用错误的令牌登录
        response=self.client.get('/api/v1.0/posts/',headers=self.get_api_headers('bad-token',''))
        self.assertEqual(response.status_code,401)

        #生成令牌
        response=self.client.get('/api/v1.0/token',headers=self.get_api_headers('json1@example.com','cat'))
        self.assertEqual(response.status_code,200)
        json_response=json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        token=json_response['token']

        #用正确的令牌登录
        response=self.client.get('/api/v1.0/posts/',headers=self.get_api_headers(token,''))
        self.assertEqual(response.status_code,200)

    def test_anonymous(self):
        '''这是对匿名用户的测试'''
        response=self.client.get('/api/v1.0/posts/',headers=self.get_api_headers('',''))
        self.assertEqual(response.status_code,401)

    def test_unconfirmed_account(self):
        '''测试未经过确认的账号'''
        #添加一个未经过确认的用户
        r=Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u=User(email='json2@example.com',password='cat',role=r,confirmed=False)
        db.session.add(u)
        db.session.commit()

        #用这个未经过确认的用户获取所有的博客列表
        response=self.client.get('/api/v1.0/posts/',headers=self.get_api_headers('json2@example.com','cat'))
        self.assertEqual(response.status_code,403)

    def test_posts(self):
        '''这是对用户写博客、编辑博客等的测试'''
        #添加一个用户
        r=Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u=User(email='json3@example.com',password='cat',confirmed=True,role=r)
        db.session.add(u)
        db.session.commit()

        #写一篇正文为空的博客
        response=self.client.post('/api/v1.0/posts/',headers=self.get_api_headers('json3@example.com','cat'),data=json.dumps({'body':''}))
        self.assertEqual(response.status_code,400)

        #写一篇合法的博客
        response=self.client.post('/api/v1.0/posts/',
        headers=self.get_api_headers('json3@example.com','cat'),
        data=json.dumps({'body':'这是博客的正文'}))
        self.assertEqual(response.status_code,201)
        #这是新博客的路由
        url=response.headers.get('Location')
        self.assertIsNotNone(url)

        #获取这篇新博客
        response=self.client.get(url,headers=self.get_api_headers('json3@example.com','cat'))
        self.assertEqual(response.status_code,200)
        json_response=json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['url'],url)
        self.assertEqual(json_response['body'],'这是博客的正文')
        self.assertEqual(json_response['body_html'],'<p>这是博客的正文</p>')
        #一会儿就要用json_response这个变量名表示别的东西了，但是这里的内容我们也需要使用，所以重命名这个变量
        json_post=json_response

        #获取这个用户的所有博客
        response=self.client.get('/api/v1.0/users/{}/posts/'.format(u.id),headers=self.get_api_headers('json3@example.com','cat'))
        self.assertEqual(response.status_code,200)
        json_response=json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count',0),1)
        self.assertEqual(json_response['posts'][0],json_post)
        
        #编辑博客
        response=self.client.put(
            url,
            headers=self.get_api_headers('json3@example.com','cat'),
            data=json.dumps({'body':'更新后的内容'}))
        self.assertEqual(response.status_code,200)
        json_response=json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['url'],url)
        self.assertEqual(json_response['body'],'更新后的内容')
        self.assertEqual(json_response['body_html'],'<p>更新后的内容</p>')

    def test_users(self):
        '''这是对用户的测试'''
        #添加两个用户
        r=Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1=User(email='jg@example.com',username='jg',password='cat',confirmed=True,role=r)
        u2=User(email='rex@example.com',username='rex',password='dog',confirmed=True,role=r)
        db.session.add_all([u1,u2])
        db.session.commit()

        #获取第一位用户
        response=self.client.get(
            '/api/v1.0/users/{}'.format(u1.id),
            headers=self.get_api_headers('rex@example.com','dog'))
        self.assertEqual(response.status_code,200)
        json_response=json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'],'jg')

        #获取第二位用户
        response=self.client.get(
            '/api/v1.0/users/{}'.format(u2.id),
            headers=self.get_api_headers('rex@example.com','dog'))
        self.assertEqual(response.status_code,200)
        json_response=json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'],'rex')

    def test_comments(self):
        '''这是对评论的测试'''
        #添加两个用户
        r=Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1=User(email='paul@example.com',username='paul',password='cat',
                confirmed=True,role=r)
        u2=User(email='john@example.com',username='john',password='dog',
                confirmed=True,role=r)
        db.session.add_all([u1,u2])
        db.session.commit()

        #添加一篇博客
        post=Post(body='这是正文',author=u1)
        db.session.add(post)
        db.session.commit()

        #写一个评论
        response=self.client.post(
            '/api/v1.0/posts/{}/comments/'.format(post.id),
            headers=self.get_api_headers('john@example.com','dog'),
            data=json.dumps({'body':'Good [post](http://example.com)!'}))
        self.assertEqual(response.status_code,201)
        json_response=json.loads(response.get_data(as_text=True))
        url=response.headers.get('Location')
        self.assertIsNotNone(url)
        self.assertEqual(json_response['body'],'Good [post](http://example.com)!')
        self.assertEqual(re.sub('<.*?>','',json_response['body_html']),'Good post!')

        #获取刚添加的这个新评论
        response=self.client.get(
            url,
            headers=self.get_api_headers('paul@example.com','cat'))
        self.assertEqual(response.status_code,200)
        json_response=json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['url'],url)
        self.assertEqual(json_response['body'],'Good [post](http://example.com)!')

        #再添加一条评论，这回直接往数据库里加
        comment=Comment(body='Thank you!',author=u1,post=post)
        db.session.add(comment)
        db.session.commit()

        #获取这两条评论
        response=self.client.get(
            '/api/v1.0/posts/{}/comments/'.format(post.id),
            headers=self.get_api_headers('john@example.com','dog'))
        self.assertEqual(response.status_code,200)
        json_response=json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('comments'))
        self.assertEqual(json_response.get('count',0),2)

        #获取所有的评论
        response=self.client.get(
            '/api/v1.0/comments/',
            headers=self.get_api_headers('john@example.com','dog'))
        self.assertEqual(response.status_code,200)
        json_response=json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('comments'))
        self.assertEqual(json_response.get('count',0),2)












