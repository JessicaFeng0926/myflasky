from flask import jsonify
from . import api
from ..exceptions import ValidationError

def forbidden(message):
    '''这是403错误的处理辅助函数'''
    response=jsonify({'error':'forbidden','message':message})
    response.status_code=403
    return response

def unauthorized(message):
    '''这是401用户密码验证失败错误的处理辅助函数'''
    response=jsonify({'error':'unauthorized','message':message})
    response.status_code=401
    return response

def bad_request(message):
    '''这是400请求不一致错误的处理辅助函数'''
    response=jsonify({'error':'bad request','message':message})
    response.status_code=400
    return response

@api.errorhandler(ValidationError)
def validation_error(e):
    '''这是处理ValidationError这个全局异常的视图'''
    return bad_request(e.args[0])