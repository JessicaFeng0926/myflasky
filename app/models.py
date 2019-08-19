from . import db
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from . import login_manager
from flask import current_app,request,url_for
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
import hashlib
from markdown import markdown
import bleach
from .exceptions import ValidationError



class Role(db.Model):
    '''这是用户角色的模型类'''
    #规定了表名
    __tablename__='roles'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(64),unique=True)
    default=db.Column(db.Boolean,default=False,index=True)
    permissions=db.Column(db.Integer)
    #在一的这方也要声明和多的那一方的关系，
    #第一个参数是模型名
    #第二个参数是允许子方使用role得到一个完整的role对象，而不只是Id
    #第三个参数是在主找子的时候产生一个支持查询的对象，而不是一个不支持查询的列表
    users=db.relationship('User',backref='role',lazy='dynamic')

    @staticmethod
    def insert_roles():
        '''向数据库里添加角色的方法'''
        roles={
            'User':(Permission.FOLLOW|
                    Permission.COMMENT|
                    Permission.WRITE_ARTICLES,True),
            'Moderator':(Permission.FOLLOW|
                         Permission.COMMENT|
                         Permission.WRITE_ARTICLES|
                         Permission.MODERATE_COMMENTS,False),
            'Administrator':(0xff,False)
        }
        for r in roles:
            role=Role.query.filter_by(name=r).first()
            if role is None:
                role=Role(name=r)
            role.permissions=roles[r][0]
            role.default=roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        '''这是返回的字符串描述'''
        return '<Role %r>' % self.name

class Follow(db.Model):
    '''这是用户关注表，是处理多对多关系的中间表'''
    __tablename__='follows'
    follower_id=db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    followed_id=db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    timestamp=db.Column(db.DateTime,default=datetime.utcnow)

class User(UserMixin,db.Model):
    '''这是用户信息的模型类'''
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    #邮箱
    email=db.Column(db.String(64),unique=True,index=True)
    #用户名
    username=db.Column(db.String(64),unique=True,index=True)
    #为了安全，数据库里不存储密码本身，而是存储密码的散列值
    password_hash=db.Column(db.String(128))
    #声明外键,参数是表名.列名
    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))
    #确认用户信息是否正确的字段（激活账号）
    confirmed=db.Column(db.Boolean,default=False)
    #姓名
    name=db.Column(db.String(64))
    #位置
    location=db.Column(db.String(64))
    #简介
    about_me=db.Column(db.Text())
    #加入本站的时间
    member_since=db.Column(db.DateTime(),default=datetime.utcnow)
    #最后活跃时间
    last_seen=db.Column(db.DateTime(),default=datetime.utcnow)
    #用户头像地址中的邮箱散列值
    avatar_hash=db.Column(db.String(32))
    #声明和博客文章模型的一对多关系
    #第一个参数是多方的类名
    #第二个参数允许blog.author的方式获取一个完整的用户对象
    #第三个参数允许主找子的时候进行筛选
    posts=db.relationship('Post',backref='author',lazy='dynamic')
    #这是关注者和被关注者的一对多关系
    followed=db.relationship('Follow',foreign_keys=[Follow.follower_id],backref=db.backref('follower',lazy='joined'),lazy='dynamic',cascade='all,delete-orphan')
    #这是被关注者和关注者的一对多关系
    followers=db.relationship('Follow',foreign_keys=[Follow.followed_id],backref=db.backref('followed',lazy='joined'),lazy='dynamic',cascade='all,delete-orphan')
    #这是和评论的一对多关系
    comments=db.relationship('Comment',backref='author',lazy='dynamic')

    def __init__(self,**kwargs):
        '''这是自定义的初始化方法，用于给新用户分配合适的角色'''
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            else:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash=hashlib.md5(self.email.encode('utf-8')).hexdigest()
        #让用户关注自己，这样就能在主页关注人里看到自己的博客
        self.follow(self)


    def generate_confirmation_token(self,expiration=3600):
        '''这是生成用于验证用户邮箱的加密口令方法'''
        s=Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'confirm':self.id})

    def confirm(self,token):
        '''这是验证上述口令是否正确的方法'''
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed=True
        db.session.add(self)
        return True

    def generate_reset_token(self,expiration=3600):
        '''这是自定义的生成重置密码口令的方法'''
        s=Serializer(current_app.config['SECRET_KEY'],expiration)
        token=s.dumps({'reset':self.id})
        return token
    
    @staticmethod
    def reset_password(token,new_password):
        '''
        这是一个静态方法，静态方法的好处是既能在类上调用，也能在实例上调用

        :参数 token:重置密码口令
        :参数 new_password:用户设置的新密码
        '''
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        #因为用户是未登录的状态，所以需要查询，也就是不存在实例
        #这种情况下用静态方法很合适
        user=User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password=new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self,new_email,expiration=3600):
        '''这是生成修改邮箱口令的方法'''
        s=Serializer(current_app.config['SECRET_KEY'],expiration)
        token=s.dumps({'change_email':self.id,'new_email':new_email})
        return token

    def change_email(self,token):
        '''这是修改邮箱的方法'''
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        #口令里的id必须等于当前用户的id
        if data.get('change_email')!=self.id:
            return False
        new_email=data.get('new_email')
        #新邮箱不能为空
        if new_email is None:
            return False
        #如果口令里的新邮箱已经被占用，那就返回False
        if User.query.filter_by(email=new_email).first():
            return False
        self.email=new_email
        #修改邮箱的时候，用户的邮箱散列值也要跟着修改
        self.avatar_hash=hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    
    @property
    def password(self):
        '''设置了一个只写的动态属性'''
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        '''这个属性有赋值的方法'''
        self.password_hash=generate_password_hash(password)
    
    def verify_password(self,password):
        '''这是验证用户输入的密码是否正确的方法'''
        return check_password_hash(self.password_hash,password)
    
    def can(self,permissions):
        '''这是判断用户有没有某些权限的方法'''
        return self.role is not None and (self.role.permissions & permissions)==permissions

    def is_administrator(self):
        '''这是判断用户是否是管理员的方法'''
        return self.can(Permission.ADMINISTER)

    def ping(self):
        '''更新用户最后访问时间的方法,这个方法会在请求钩子里调用'''
        self.last_seen=datetime.utcnow()
        db.session.add(self)

    def gravatar(self,size=100,default='identicon',rating='g'):
        '''这是生成用户头像url的方法'''
        if request.is_secure:
            url='https://secure.gravatar.com/avatar'
        else:
            url='http://www.gravatar.com/avatar'
        hash=self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url,hash=hash,size=size,default=default,rating=rating)
    
    @staticmethod
    def generate_fake(count=100):
        '''这是生成大量测试数据的方法'''
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u=User(email=forgery_py.internet.email_address(),
            username=forgery_py.internet.user_name(True),
            password=forgery_py.lorem_ipsum.word(),
            confirmed=True,
            name=forgery_py.name.full_name(),
            location=forgery_py.address.city(),
            about_me=forgery_py.lorem_ipsum.sentence(),
            member_since=forgery_py.date.date(True))

            db.session.add(u)
            try:
                db.session.commit()
            #当用户名或邮箱重复的时候，回滚
            except IntegrityError:
                db.session.rollback()
    
    def follow(self,user):
        '''这是关注别人'''
        if not self.is_following(user):
            f=Follow(follower=self,followed=user)
            db.session.add(f)

    def unfollow(self,user):
        '''这是取关'''
        #这里用到了通过中间表查询，self.followed能查出当前用户关注的所有人
        f=self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self,user):
        '''这是判断是否关注了某人，返回布尔值'''
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self,user):
        '''这是判断某人是否是当前用户的粉丝,返回布尔值'''
        return self.followers.filter_by(follower_id=user.id).first() is not None
    
    @property
    def followed_posts(self):
        '''这是查询出用户关注的人发布的所有博客,它是一个动态属性'''
        return Post.query.join(Follow,Follow.followed_id==Post.author_id).filter(Follow.follower_id==self.id)
    
    @staticmethod
    def add_self_follows():
        '''这个静态方法用于让现有的用户都关注自己'''
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()
    
    def generate_auth_token(self,expiration):
        '''这是生成登录密令的方法'''
        s=Serializer(current_app.config['SECRET_KEY'],expires_in=expiration)
        return s.dumps({'id':self.id}).decode('utf-8')
    
    @staticmethod
    def verify_auth_token(token):
        '''这是验证登录密令的方法'''
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token.encode('utf-8'))
        except:
            return None
        return User.query.get(data['id'])

    def to_json(self):
        '''这是把用户信息转化为json的方法'''
        json_user={
            'url':url_for('api.get_user',id=self.id,_external=True),
            'username':self.username,
            'member_since':self.member_since,
            'last_seen':self.last_seen,
            'posts':url_for('api.get_user_posts',id=self.id,_external=True),
            'followed_posts':url_for('api.get_user_followed_posts',id=self.id,_external=True),
            'posts_count':self.posts.count()
        }
        return json_user

    def __repr__(self):
        '''这是返回的描述'''
        return '<User %r>'%self.username

class Permission():
    '''这是权限常量的类'''
    FOLLOW=0x01   #十进制的1
    COMMENT=0x02  #十进制的2
    WRITE_ARTICLES=0x04   #十进制的4
    MODERATE_COMMENTS=0x08   #十进制的8
    ADMINISTER=0x80    #十进制的128

class AnonymousUser(AnonymousUserMixin):
    '''这是匿名用户类，继承自flask-login提供的匿名用户类'''
    def can(self,permissions):
        return False
    def is_administrator(self):
        return False

#把我们的自定义类赋给用户未登录时的用户对象
login_manager.anonymous_user=AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    '''这是加载用户的回调函数'''
    return User.query.get(int(user_id))

class Post(db.Model):
    '''这是博客文章的模型类'''
    __tablename__='posts'
    id=db.Column(db.Integer,primary_key=True)
    #正文
    body=db.Column(db.Text)
    #时间戳
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    #外键，绑定用户表
    author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    #这是保存html版本的博客正文的字段
    body_html=db.Column(db.Text)
    #这是和评论的一对多关系
    comments=db.relationship('Comment',backref='post',lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        '''这是随机生成大量测试博文的方法'''
        from random import randint,seed
        import forgery_py

        seed()
        user_count=User.query.count()
        for i in range(count):
            u=User.query.offset(randint(0,user_count-1)).first()
            p=Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
            timestamp=forgery_py.date.date(True),
            author=u)
            db.session.add(p)
            db.session.commit()
    
    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        '''这是把markdown原文转换成html的方法'''
        allowed_tags=['a','abbr','acronym','b','blockquote','code','em','i','li','ol','pre','strong','ul','h1','h2','h3','p']
        target.body_html=bleach.linkify(bleach.clean(markdown(value,output_format='html'),tags=allowed_tags,strip=True))
    
    def to_json(self):
        '''这是把博客文章转化为json格式的方法'''
        json_post={
            'url':url_for('api.get_post',id=self.id,_external=True),
            'body':self.body,
            'body_html':self.body_html,
            'timestamp':self.timestamp,
            'author':url_for('api.get_user',id=self.author_id,_external=True),
            'comments':url_for('api.get_post_comments',id=self.id,_external=True),
            'comment_count':self.comments.count()}
        return json_post  
    
    @staticmethod
    def from_json(json_post):
        '''这是从json格式创建一片博客文章的方法'''
        body=json_post.get('body')
        if body is None or body =='':
            raise ValidationError('正文不存在')
        return Post(body=body)

db.event.listen(Post.body,'set',Post.on_changed_body)


class Comment(db.Model):
    '''这是用户评论的模型类'''
    __tablename__='comments'
    id=db.Column(db.Integer,primary_key=True)
    #这是存放的评论内容的原始数据
    body=db.Column(db.Text)
    #html版的评论内容
    body_html=db.Column(db.Text)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    disabled=db.Column(db.Boolean)
    #这是评论发出者的id，是个外键
    author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    post_id=db.Column(db.Integer,db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        '''这是把评论原数据转化为html并存进相应字段的方法'''
        allowed_tags=['a','abbr','acronym','b','code','em','i','strong']
        target.body_html=bleach.linkify(bleach.clean(markdown(value,output_format='html'),tags=allowed_tags,strip=True))
    
    def to_json(self):
        '''这是把评论内容转化为json的方法'''
        json_comment={
            'url':url_for('api.get_comment',id=self.id,_external=True),
            'post':url_for('api.get_post',id=self.id,_external=True),
            'body':self.body,
            'body_html':self.body_html,
            'timestamp':self.timestamp,
            'author':url_for('api.get_user',id=self.author_id,_external=True)
        }
        return json_comment
    
    @staticmethod
    def from_json(json_comment):
        '''这是从json创建新评论的方法'''
        body=json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('评论正文不能为空')
        return Comment(body=body)

db.event.listen(Comment.body,'set',Comment.on_changed_body)
