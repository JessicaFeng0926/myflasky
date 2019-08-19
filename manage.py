import os

COV=None
if os.environ.get('FLASKY_COVERAGE'):
    import coverage
    COV=coverage.Coverage(branch=True,include='app/*')
    COV.start()


from app import create_app,db
from app.models import Role,User,Post,Comment,Permission,Follow
from flask_script import Manager,Shell
from flask_migrate import Migrate,MigrateCommand

#创建程序
app=create_app(os.environ.get('FLASK_CONFIG') or 'default')

#初始化命令行和迁移
manager=Manager(app)
migrate=Migrate(app,db)


def make_shell_context():
    return dict(db=db,User=User,Role=Role,Post=Post,Comment=Comment,Permission=Permission,Follow=Follow)

#以后在shell里就不需要导入上面字典里列出的这些了
manager.add_command('shell',Shell(make_context=make_shell_context))
#以后可以用db作为迁移的命令
manager.add_command('db',MigrateCommand)

#自定义启动单元测试的命令
@manager.command
def test(coverage=False):
    '''这是启动单元测试的函数，用函数名作为命令'''
    if coverage and not os.environ.get('FLASKY_COVERAGE'):
        import sys
        os.environ['FLASKY_COVERAGE']='1'
        os.execvp(sys.executable,[sys.executable]+sys.argv)

    import unittest
    tests=unittest.TestLoader().discover('tests')
    #其实现在这个verbosity写不写都无所谓了，模块已经很智能，自己就能算出来跑了多少个测试
    unittest.TextTestRunner(verbosity=8).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('覆盖总结：')
        COV.report()
        basedir=os.path.abspath(os.path.dirname(__file__))
        covdir=os.path.join(basedir,'tmp/coverage/')
        COV.html_report(directory=covdir)
        print('HTML 版本:'+ os.path.abspath(os.path.join(covdir,'index.html')))
        COV.erase()

#basedir=os.path.abspath(os.path.dirname(__file__))
#the_profile_dir=os.path.abspath(os.path.join(basedir,'profile'))
@manager.command
def profile(length=25,profile_dir=None):
    '''
    这是在分析器的监测下启动程序，这样就能检测到那些耗时的运算了

    :参数 length:
    :参数 profile_dir:
    '''
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app=ProfilerMiddleware(app.wsgi_app,restrictions=[length],profile_dir=profile_dir)
    app.run()

@manager.command
def deploy():
    '''这是执行部署的相关工作'''
    from flask_migrate import upgrade
    from app.models import Role,User

    #把数据库更新到最新版本
    upgrade()

    #创建用户角色
    Role.insert_roles()

    #让所用用户都关注自己
    User.add_self_follows()



if __name__ == '__main__':
    manager.run()