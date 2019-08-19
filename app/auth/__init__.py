from flask import Blueprint

auth=Blueprint('auth',__name__)

#导入当前目录里的views
from . import views

