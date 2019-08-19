from flask import Flask
#从请求上下文引入request对象，这样就能把它当做全局变量使用，不需要每个视图都有这个参数
from flask import request
from flask import make_response
from flask import redirect
#这个函数可以处理错误的请求，返回404页面
from flask import abort
#这是从命令行扩展里导入了类,注意导入的方法跟书上不一样了
from flask_script import Manager,Server,Shell
#导入bootstrap
from flask_bootstrap import Bootstrap
#导入渲染模板的函数
from flask import render_template
from datetime import datetime
#从管理时间的扩展中导入一个类
from flask_moment import Moment
#导入自定义的表单类
from forms import NameForm
#导入用于反向解析url的函数，导入用户会话和用于显示消息的flash
from flask import url_for,session,flash
#导入用于处理数据库的类
from flask_sqlalchemy import SQLAlchemy
#导入os，用于处理路径
import os
#导入跟迁移相关的扩展
from flask_migrate import Migrate,MigrateCommand
#从邮件扩展中导入类
from flask_mail import Mail,Message
#多线程
from threading import Thread

#生成当前文件的路径
basedir=os.path.abspath(os.path.dirname(__file__))


#规定主程序在哪里
app=Flask(__name__)

#配置数据库
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(basedir,'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']=True
#生成数据库管理类的实例
db=SQLAlchemy(app)

#配置密钥
app.config['SECRET_KEY']='LYP82yeardelafei'

#生成一个Manager的实例
manager=Manager(app)
#这一行能够保证我们启动服务器的时候是以debug模式开启的，否则debug模式默认关闭
manager.add_command('runserver',Server(use_debugger=True))
#生成一个bootstrap实例
bootstrap=Bootstrap(app)
#生成了一个管理时间的moment实例
moment=Moment(app)

#生成迁移的实例
migrate=Migrate(app,db)
manager.add_command('db',MigrateCommand)


#配置邮件需要的参数
app.config['MAIL_SERVER']='smtp.qq.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USE_SSL']=True
#为了保障信息安全，邮箱和密码要保存在环境变量里面，不能直接写进脚本
app.config['MAIL_USERNAME']=os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD']=os.environ.get('MAIL_PASSWORD')
#生成邮件实例
mail=Mail(app)

#在app的配置字典里存入一个邮件主题的前缀
app.config['FLASKY_MAIL_SUBJECT_PREFIX']='[Flasky]'
app.config['FLASKY_ADMIN']=os.environ.get('FLASK_ADMIN')

def send_mail(to,subject,template,**kwargs):
    '''
    这是自己封装的发邮件的函数

    :参数 to:收件人的邮箱
    :参数 subject:邮件主题
    :参数 template:邮件正文路径，不包括扩展名
    :参数 **kwargs:这是要传给模板的包裹关键字参数
    '''
    msg=Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX']+subject,sender=app.config['MAIL_USERNAME'],recipients=[to])
    msg.html=render_template(template+'.html',**kwargs)
    #mail.send(msg)
    #新版本的该函数启用异步发邮件
    thr=Thread(target=send_async_email,args=(app,msg))
    thr.start()
    return thr



def send_async_email(app,msg):
    '''
    这是异步发送邮件的函数，它会被send_mail函数调用

    :参数 app:是我们的应用
    :参数 msg:是我们邮件消息对象
    '''
    with app.app_context():
        mail.send(msg)


#这个装饰器负责给视图分配路由
@app.route('/')
def index():
    return '<h1>Hello World!</h1>',400

#尖括号里的是一个变量，程序可以接收，就像Django里的(\d+)一样，这里的name是字符串
#如果想要接收数字，需要声明是整数类型<int:blog_id>
@app.route('/user/<name>')
def user(name):
    #接收url里的变量，并经由视图返回到前端，这样就能在前端生成个性化的欢迎信息
    #return '<h1>Hello %s!</h1>'%name
    #下面使用模板，第二个参数是关键字参数，除了用两个星号和字典传参，还可以用name=name的形式传参
    current_time=datetime.utcnow()
    return render_template('user.html',**{'name':name,'current_time':current_time})

#request的headers里面有用户代理的信息
@app.route('/agent')
def agent():
    user_agent=request.headers.get('User-Agent')
    return '<p>Your agent is %s</p>'%user_agent

#这个例子展示了使用response对象以及给它设置cookie
@app.route('/cookie')
def cookie():
    response=make_response('<h1>它带了cookie</h1>')
    #和django设置cookie的方法一样
    #注意cookie的键和值都必须是字符串，不能是数字
    response.set_cookie('answer','42')
    return response

#这个例子展示了重定向
@app.route('/redirecturl')
def redirecturl():
    #当请求redirecturl这个路由的时候，就会重定向到百度的首页
    return redirect('https://www.baidu.com')

#这个例子展示请求的页面不存在时，返回404
@app.route('/users/<id>')
def get_user(id):
    if int(id) not in [1,2,3]:
        #abort函数处理错误请求
        abort(404)
    return '<h1>用户存在</h1>'

#自定义404页面
@app.errorhandler(404)
def page_not_found(e):
    return '<h1>页面不存在</h1>'

#这是提交表单数据的例子
@app.route('/form',methods=['GET','POST'])
def form():
    #name=''
    nameform=NameForm()
    if nameform.validate_on_submit():
        #name=nameform.name.data
        old_name=session.get('name')
        if old_name and old_name!=nameform.name.data:
            flash('您更换了名字')
        session['name']=nameform.name.data
        nameform.name.data=''
        
        return redirect(url_for('form'))
    return render_template('nameform.html',nameform=nameform,name=session.get('name'))

#这是视图和数据库交互的示例
@app.route('/data',methods=['GET','POST'])
def data():
    nameform=NameForm()
    if nameform.validate_on_submit():
        user=User.query.filter_by(username=nameform.name.data).first()
        if user:
            session['known']=True
        else:
            
            session['known']=False
            newuser=User(username=nameform.name.data,role_id=2)
            db.session.add(newuser)
            send_mail(app.config['FLASKY_ADMIN'],'新用户','mail/new_user',user=newuser)
        session['name']=nameform.name.data
        nameform.name.data=''
        return redirect(url_for('data'))
    return render_template('nameform.html',name=session.get('name'),nameform=nameform,known=session.get('known',False))



#模型示例
class Role(db.Model):
    '''这是用户角色的模型类'''
    #规定了表名
    __tablename__='roles'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(64),unique=True)
    #在一的这方也要声明和多的那一方的关系，
    #第一个参数是模型名
    #第二个参数是允许子方使用role得到一个完整的role对象，而不只是Id
    #第三个参数是在主找子的时候产生一个支持查询的对象，而不是一个不支持查询的列表
    users=db.relationship('User',backref='role',lazy='dynamic')

    def __repr__(self):
        '''这是返回的字符串描述'''
        return '<Role %r>' % self.name

class User(db.Model):
    '''这是用户信息的模型类'''
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(64),unique=True,index=True)
    #声明外键,参数是表名.列名
    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))

    def __repr__(self):
        '''这是返回的描述'''
        return '<User %r>'%self.username


#为shell命令注册一个回调函数，这样每次启动shell，我们需要用的模型和数据库管理示例就自动导入了
def make_shell_context():
    return dict(app=app,db=db,User=User,Role=Role)
#让shell命令的回调函数等于我们自定义的函数
manager.add_command('shell',Shell(make_context=make_shell_context))

if __name__ == '__main__':
    #这是启动程序的入口，参数是debug=True,这适用于开发环境
    #app.run(debug=True)
    #已经有了命令行实例manager，就可以换一种启动程序的方式了
    manager.run()



