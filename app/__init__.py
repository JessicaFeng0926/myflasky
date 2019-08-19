from flask import Flask,render_template
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
from flask_pagedown import PageDown

#实例化一些我们需要用到的类
bootstrap=Bootstrap()
mail=Mail()
moment=Moment()
db=SQLAlchemy()
login_manager=LoginManager()
login_manager.session_protection='strong'
login_manager.login_view='auth.login'
pagedown=PageDown()

def create_app(config_name):
    '''
    这是用于创建程序实例的工厂函数

    :参数 config_name:这是配置名，也就是我们自定义的config.py中的config字典的键
    '''
    app=Flask(__name__)
    #这是Flaskapp.config的方法，它需要的参数是一个配置类
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    #初始化这些要用到的扩展类的实例
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    #附加路由和自定义的错误页面

    #导入并注册蓝本
    from .main import main as main_blueprint
    #这是主页的蓝本
    app.register_blueprint(main_blueprint)
    from .auth import auth as auth_blueprint
    #这是跟用户认证相关的蓝本
    app.register_blueprint(auth_blueprint,url_prefix='/auth')
    #这是api蓝本
    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint,url_prefix='/api/v1.0')
    
    return app



