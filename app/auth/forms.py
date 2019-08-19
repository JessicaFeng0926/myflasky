from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import Required,Email,Length,Regexp,EqualTo
from wtforms import ValidationError
from ..models import User



class LoginForm(FlaskForm):
    '''这是登录表单类'''
    email=StringField('邮箱',validators=[Required(),Length(1,64),Email()])
    password=PasswordField('密码',validators=[Required()])
    remember_me=BooleanField('记住我')
    submit=SubmitField('登录')

class RegistrationForm(FlaskForm):
    '''这是注册表单类'''
    email=StringField('邮箱',validators=[Required(),Length(1,64),Email()])
    username=StringField('用户名',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'用户名只能有字母、数字、下划线和点')])
    password=PasswordField('密码',validators=[Required(),EqualTo('password2',message='两次密码输入必须一致')])
    password2=PasswordField('确认密码',validators=[Required()])
    submit=SubmitField('注册')

    def validate_email(self,field):
        '''这是自定义的对邮箱的进一步验证'''
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被占用')

    def validate_username(self,field):
        '''这是自定义的对用户名的进一步验证'''
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被占用')

class ChangePasswordForm(FlaskForm):
    '''这是修改密码的表单类'''
    old_password=PasswordField('旧密码',validators=[Required()])
    password=PasswordField('新密码',validators=[Required(),EqualTo('password2',message='两次输入的新密码应保持一致')])
    password2=PasswordField('确认新密码',validators=[Required()])
    submit=SubmitField('提交')

class ResetPasswordRequestForm(FlaskForm):
    '''这是发起重置密码请求的表单类'''
    email=StringField('邮箱',validators=[Required(),Email()])
    submit=SubmitField('提交')

class ResetPasswordForm(FlaskForm):
    '''这是重置密码的表单类'''
    password=PasswordField('新密码',validators=[Required(),EqualTo('password2',message='两次输入的密码不一致')])
    password2=PasswordField('确认新密码',validators=[Required()])
    submit=SubmitField('提交')

class ChangeEmailForm(FlaskForm):
    '''这是修改邮箱的表单类'''
    email=StringField('新邮箱',validators=[Required(),Email()])
    password=PasswordField('密码',validators=[Required()])
    submit=SubmitField('提交')

    def validate_email(self,field):
        '''这是对新邮箱的进一步验证'''
        user=User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('该邮箱已被占用')




    
