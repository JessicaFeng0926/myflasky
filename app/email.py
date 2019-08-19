from flask_mail import Message
from app import mail
from threading import Thread
from flask import render_template,current_app



def send_async_mail(app,msg):
    '''
    这是异步发送邮件的函数

    :参数 app:当前活动的app
    :参数 msg:邮件里要发送的消息
    '''
    with app.app_context():
        mail.send(msg)

def send_email(to,subject,template,**kwargs):
    '''
    这是自定义的发邮件的函数
    
    :参数 to:收件人的邮箱
    :参数 subject:邮件主题
    :参数 template:邮件正文模板
    :参数 **kwargs:这是给模板用的包裹关键字参数
    '''
    app=current_app._get_current_object()
    msg=Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX']+subject,sender=app.config['FLASKY_MAIL_SENDER'],recipients=[to])
    msg.html=render_template(template+'.html',**kwargs)
    t=Thread(target=send_async_mail,args=(app,msg))
    t.start()
    return t


