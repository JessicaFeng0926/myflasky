from flask import render_template,redirect,request,url_for,flash
from . import auth
from .forms import LoginForm,RegistrationForm,ChangePasswordForm,ResetPasswordRequestForm,ResetPasswordForm,ChangeEmailForm
from ..models import User
from flask_login import login_user,login_required,logout_user,current_user
from ..email import send_email
from .. import db

#登录的路由和视图
@auth.route('/login',methods=['GET','POST'])
def login():
    '''这是登录的视图'''
    form=LoginForm()
    if form.validate_on_submit():
        #查找用户是否在数据库里
        user=User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user,form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('用户名或密码错误')
    return render_template('auth/login.html',form=form)

#登出路由和视图
@auth.route('/logout')
def logout():
    '''这是登出的视图'''
    logout_user()
    flash('您已退出登录')
    return redirect(url_for('main.index'))

#注册的路由和视图
@auth.route('/register',methods=['GET','POST'])
def register():
    '''这是注册的视图'''
    form=RegistrationForm()
    if form.validate_on_submit():
        user=User(email=form.email.data,
                username=form.username.data,
                password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token=user.generate_confirmation_token()
        send_email(user.email,'确认您的账号','auth/email/confirm',user=user,token=token)
        flash('已经向您的邮箱发送了确认邮件，请尽快查收')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html',form=form)

#确认账号的路由和视图
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    '''
    这是确认账号的视图

    :参数 token:从url里接收到的加密确认口令
    '''
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('您的账号已经成功确认，非常感谢！')
    else:
        flash('该链接有误或已过期')
    return redirect(url_for('main.index'))

#定义一个请求钩子，限制已登录但未确认邮箱的用户访问一些页面
@auth.before_app_request
def before_request():
    '''这是自定义的请求钩子'''
    if current_user.is_authenticated:
        #只要是已登录的用户，就更新他的最新访问时间
        current_user.ping()
        if not current_user.confirmed and request.endpoint[:5]!='auth.' and request.endpoint!='static':
            return redirect(url_for('auth.unconfirmed'))

#未确认页面的路由和视图
@auth.route('/unconfirmed')
def unconfirmed():
    '''未确认页面的视图'''
    #未登录用户或者是已确认的用户就重定向到首页
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    #已登录的未确认用户留在这个页面
    return render_template('auth/unconfirmed.html')

#重新发送确认邮件的路由和视图
@auth.route('/confirm')
@login_required
def resend_confirmation():
    '''这是重新发送确认邮件的视图'''
    token=current_user.generate_confirmation_token()
    send_email(current_user.email,'确认您的账号','auth/email/confirm',user=current_user,token=token)
    flash('新的确认邮件已发送至您的邮箱，请尽快查收')
    return redirect(url_for('main.index'))

#下面是修改密码的路由和视图
@auth.route('/change_password',methods=['GET','POST'])
@login_required
def change_password():
    '''这是修改密码的视图'''
    form=ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password=form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('您的密码已修改')
            return redirect(url_for('main.index'))
        else:
            flash('您的密码有误')
    return render_template('auth/change_password.html',form=form)


#发起重置密码请求的路由和视图
@auth.route('/reset_password_request',methods=['GET','POST'])
def reset_password_request():
    '''这是发起重置密码请求的视图'''
    form=ResetPasswordRequestForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user:
            token=user.generate_reset_token()
            send_email(form.email.data,'重置密码','auth/email/reset_password_email',token=token,user=user)
            flash('重置密码邮件已发送至您的邮箱，请尽快查收并按照提示完成密码重置')
            return redirect(url_for('auth.login'))
        else:
            flash('邮箱错误')
    return render_template('auth/reset_password_request.html',form=form)

#这是完成密码重置的路由和视图
@auth.route('/reset_password/<token>',methods=['GET','POST'])
def reset_password(token):
    '''
    这是重置密码的视图

    :参数 token:url里的重置密码口令
    '''
    form=ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_password(token,form.password.data):
            flash('您的密码已重置')
            db.session.commit()
            return redirect(url_for('auth.login'))
        else:
            flash('您的重置密码链接有误或已失效')
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html',form=form)

#这是修改邮箱的路由和视图
@auth.route('/change_email',methods=['GET','POST'])
@login_required
def change_email_request():
    '''这是修改邮箱的视图'''
    form=ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            token=current_user.generate_email_change_token(form.email.data)
            send_email(form.email.data,'修改邮箱','auth/email/change_email',user=current_user,token=token)
            flash('已经向您的新邮箱发送了邮件，请尽快查收并完成邮箱修改')
        else:
            flash('密码错误')
    return render_template('auth/change_email_request.html',form=form)

#这是完成邮箱修改的路由和视图
@auth.route('/change_email/<token>')
@login_required
def change_email(token):
    '''这是完成邮箱修改的视图'''
    if current_user.change_email(token):
        db.session.commit()
        flash('您的邮箱已成功修改')
    else:
        flash('您的修改链接有误或已过期')
    return redirect(url_for('main.index'))


