from functools import wraps
from .errors import forbidden
from flask import g

def permission_required(permission):
    '''这是API专用的验证权限的装饰器的外壳'''
    def decorator(f):
        @wraps(f)
        def decorated_function(*args,**kwargs):
            if not g.current_user.can(permission):
                return forbidden('Insufficient permissions')
            return f(*args,**kwargs)
        return decorated_function
    return decorator




