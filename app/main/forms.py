#从表单验证的扩展中导入表单类
from flask_wtf import FlaskForm
#导入字段类
from wtforms import StringField,SubmitField,TextAreaField,BooleanField,SelectField
#导入用于验证的函数
from wtforms.validators import Required,Length,Regexp,Email
from wtforms import ValidationError
from ..models import Role,User
from flask_pagedown.fields import PageDownField

class NameForm(FlaskForm):
    '''这是自定义的姓名表单类'''
    name=StringField('请输入您的姓名',validators=[Required()])
    submit=SubmitField('提交')

class EditProfileForm(FlaskForm):
    '''这是用户级别的编辑个人资料的表单'''
    name=StringField('真实姓名',validators=[Length(0,64)])
    location=StringField('地区',validators=[Length(0,64)])
    about_me=TextAreaField('个人简介')
    submit=SubmitField('提交')

class EditProfileAdminForm(FlaskForm):
    '''这是管理员级别的编辑用户资料的表单'''
    email=StringField('邮箱',validators=[Required(),Length(1,64),Email()])
    username=StringField('用户名',validators=[Required(),Length(1,64),Regexp(r'^[\u4E00-\u9FA5A-Za-z][\u4E00-\u9FA5A-Za-z_.]*$',0,'用户名只能有汉字、英文字母、数字、点和下划线')])
    confirmed=BooleanField('是否确认')
    role=SelectField('角色',coerce=int)
    name=StringField('真实姓名',validators=[Length(0,64)])
    location=StringField('地区',validators=[Length(0,64)])
    about_me=TextAreaField('个人简介')
    submit=SubmitField('提交')

    def __init__(self,user,*args,**kwargs):
        '''这是初始化方法'''
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)
        self.role.choices=[(role.id,role.name) for role in Role.query.order_by(Role.name).all()]
        self.user=user

    def validate_email(self,field):
        '''这是进一步验证邮箱的方法'''
        #如果管理员修改了用户的邮箱，而这个新邮箱又是被其他用户占用的，那就报错
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被占用')

    def validate_username(self,field):
        '''这是进一步验证用户名的方法'''
        if field.data!=self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被占用')

class PostForm(FlaskForm):
    '''这是用户写博客文章的表单类'''
    #博客正文输入控件换成markdown
    body=PageDownField('此刻有什么想法？',validators=[Required()])
    submit=SubmitField('提交')

class CommentForm(FlaskForm):
    '''这是用户评论的表单类'''
    body=PageDownField('',validators=[Required()])
    submit=SubmitField('评论')

