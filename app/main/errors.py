from flask import render_template,jsonify,request
from . import main

@main.app_errorhandler(404)
def page_not_found(e):
    '''这是404视图，现在它用的装饰器不是直接来自app，
    而是来自蓝本，这样创建的路由是休眠的'''

    #下面这个判断是针对api接口的
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response=jsonify({'error':'not found'})
        response.status_code=404
        return response
    print(e.description)
    print(e.response)
    return render_template('404.html'),404

@main.app_errorhandler(500)
def internal_server_error(e):
    '''这是500视图'''
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response=jsonify({'error':'internal server error'})
        response.status_code=500
        return response
    return render_template('500.html'),500

@main.app_errorhandler(403)
def permission_denied(e):
    '''这是403没有权限禁止访问的视图'''
    return render_template('403.html'),403

    


