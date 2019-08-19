from flask import Blueprint
from ..models import Permission

#实例化蓝本类，第一个参数是蓝本的名字，第二个参数是蓝本所在的模块
main=Blueprint('main',__name__)

#导入包含路由的views模块和包含错误信息处理的errors模块
#之所以在末尾导入，是因为views和errors也要导入蓝本，这是为了避免循环导包
from . import views,errors

#用上下文处理器实现每次渲染模板都传入参数Permission以供模板使用
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

