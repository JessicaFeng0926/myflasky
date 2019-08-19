from flask_httpauth import HTTPBasicAuth
from .errors import unauthorized,forbidden
from ..models import AnonymousUser,User
from flask import jsonify,g
from . import api

#初始化这个类，因为只在api中使用，所以就不在app的构造文件中初始化了
auth=HTTPBasicAuth()

@auth.verify_password
def verify_password(email_or_token,password):
    '''用户认证视图'''
    #没有传来的email，就设置为匿名用户
    if email_or_token == '':
        g.current_user=AnonymousUser()
        return False
    if password == '':
        g.current_user=User.verify_auth_token(email_or_token)
        g.token_used=True
        return g.current_user is not None
    user=User.query.filter_by(email=email_or_token).first()
    #如果用户不存在，返回False
    if not user:
        return False
    g.current_user=user
    g.token_used=False
    #如果用户存在，就根据密码是否正确返回True或者False
    return user.verify_password(password)

@auth.error_handler
def auth_error():
    '''401错误处理视图'''
    return unauthorized('Invalid credentials')

#因为这个蓝本里的所有路由都需要同样的登录保护，所以直接定义一个大家都可以用的请求钩子
@api.before_request
@auth.login_required
def before_request():
    '''这是请求钩子，在每次访问路由前都会先执行它来进行判断'''
    #对于那些登录了，却还没有验证邮箱的用户，要返回403错误
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('账号还未认证')

#下面是获取加密令牌的路由和视图
@api.route('/token')
def get_token():
    '''这是获取加密令牌的视图'''
    #匿名用户不能获取加密令牌，已经使用了令牌的不能重复获取
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token':g.current_user.generate_auth_token(expiration=360),'expiration':360})


