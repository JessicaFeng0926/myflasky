import os

#当前路径
basedir=os.path.abspath(os.path.dirname(__file__))

class Config():
    '''这是通用配置'''
    SECRET_KEY=os.environ.get('SECRET_KEY') or 'hard to guess string'
    #下面这行设置确保了只要db.session.add操作执行了，数据就会被自动提交到数据库里，不需要commit了
    SQLALCHEMY_COMMIT_ON_TEARDOWN=True
    FLASKY_MAIL_SUBJECT_PREFIX='[FLASKY]'
    FLASKY_MAIL_SENDER=os.environ.get('MAIL_USERNAME')
    FLASKY_ADMIN=os.environ.get('FLASKY_ADMIN')
    #下面是每页显示的博客数量，如果没有设置，就用默认的20
    FLASKY_POSTS_PER_PAGE=os.environ.get('FLASKY_POSTS_PER_PAGE') or 20
    #下面是每页显示的粉丝/关注人的数量，如果没有设置，就用默认的20
    FLASKY_FOLLOWERS_PER_PAGE=os.environ.get('FLASKY_FOLLOWERS_PER_PAGE') or 20
    #下面是单独的博客页面每页显示的评论数量，如果没有设置，就用默认的20
    FLASKY_COMMENTS_PER_PAGE=os.environ.get('FLASKY_COMMENTS_PER_PAGE') or 20
    #下面这个设置是允许在所有环境下使用SQLAlchemy的监测数据库查询速度的功能
    SQLALCHEMY_RECORD_QUERIES=True
    #下面是我们自己设置的一个阈值，超过0.5秒的查询被我们视为耗时查询
    FLASKY_SLOW_DB_QUERY_TIME=0.5
    @staticmethod
    def init_app(app):
        '''
        这是初始化app的静态方法，静态方法不需要形参cls和self
        '''
        pass

class DevelopmentConfig(Config):
    '''这是开发环境配置，继承自通用配置'''
    DEBUG=True
    MAIL_SERVER='smtp.qq.com'
    MAIL_PORT=465
    MAIL_USE_SSL=True
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI=os.environ.get('DEV_DATABASE_URL') or 'sqlite:///'+os.path.join(basedir,'data-dev.sqlite')


class TestingConfig(Config):
    '''这是测试环境配置，继承自通用配置'''
    TESTING=True
    #在测试环境中，把csrf关闭，这样就能避免操作csrf密令这个繁琐的工作了
    WTF_CSRF_ENABLED=False
    SQLALCHEMY_DATABASE_URI=os.environ.get('TEST_DATABASE_URL') or 'sqlite:///'+os.path.join(basedir,'data-test.sqlite')

class ProductionConfig(Config):
    '''这是生产环境配置，继承自通用配置'''
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') or 'sqlite:///'+os.path.join(basedir,'data.sqlite')
    
    #下面的配置用于把程序错误的日志发送给管理员
    import logging
    from logging.handlers import SMTPHandler
    credentials=None
    secure=None
    if getattr(cls,'MAIL_USERNAME',None) is not None:
        credentials=(cls.MAIL_USERNAME,cls.MAIL_PASSWORD)
        if getattr(cls,'MAIL_USE_SSL',None):
            secure=()
    mail_handler=SMTPHandler(
        mailhost=(cls.MAIL_SERVER,cls.MAIL_PORT),
        fromaddr=cls.FLASKY_MAIL_SENDER,
        toaddrs=[cls.FLASKY_ADMIN],
        subject=cls.FLASKY_MAIL_SUBJECT_PREFIX+'Application Error',
        credentials=credentials,
        secure=secure)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

config={
    'development':DevelopmentConfig,
    'testing':TestingConfig,
    'production':ProductionConfig,
    'default':DevelopmentConfig,
}




