from flask import render_template,redirect,session,request,url_for,abort,flash,current_app,make_response
from datetime import datetime
from . import main
from .forms import NameForm,EditProfileForm,EditProfileAdminForm,PostForm,CommentForm
from .. import db
from ..models import User,Permission,Role,Post,Comment
from ..decorators import admin_required,permission_required
from flask_login import login_required,current_user
from flask_sqlalchemy import get_debug_queries

@main.route('/',methods=['GET','POST'])
def index():
    form=PostForm()
    #如果用户有写文章的权限并且提交通过了验证
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post=Post(body=form.body.data,author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('main.index'))

    show_followed=False
    if current_user.is_authenticated:
        show_followed=bool(request.cookies.get('show_followed',''))
    if show_followed:
        #followed_posts是一个动态属性，不是方法
        query=current_user.followed_posts
    else:
        query=Post.query

    #从url里用?连接的那些参数中获取页码，如果没有获取到，就返回默认的1，
    # 第三个参数保证获取的参数无法转换成整数的时候也返回默认的1
    page=request.args.get('page',1,type=int)
    #生成分页对象，第一个参数是页码，第二个参数是每页的博客数量，默认是20，这我们用了自定义的环境变量的值
    #第三个参数使得页数超过范围的时候返回空白列表而不是报错
    pagination=query.order_by(Post.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    #博客列表换成当前页码对应的那些博客
    posts=pagination.items
    #pagination在生成页码列表的时候很有用，所以要传回去
    return render_template('index.html',form=form,posts=posts,pagination=pagination,show_followed=show_followed)

#两个用权限装饰器的例子
@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
    '''只有管理员能访问这个页面'''
    return 'For administrators!'

@main.route('/moderator')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def for_moderators_only():
    '''必须有协管员的权限才能访问该页面'''
    return 'For comment moderators!'

#下面是用户资料页的路由和视图
@main.route('/user/<username>')
def user(username):
    '''
    这是用户资料页的视图

    :参数 username:用户名
    '''
    user=User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    #查找出该用户所有的文章
    posts=user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html',user=user,posts=posts)

#下面是用户级别的个人资料编辑路由和视图
@main.route('/edit_profile',methods=['GET','POST'])
def edit_profile():
    '''这是用户级别的个人资料编辑视图'''
    form=EditProfileForm()
    if form.validate_on_submit():
        current_user.name=form.name.data
        current_user.location=form.location.data
        current_user.about_me=form.about_me.data
        db.session.add(current_user)
        flash('您的个人资料已经成功修改')
        return redirect(url_for('main.user',username=current_user.username))
    form.name.data=current_user.name
    form.location.data=current_user.location
    form.about_me.data=current_user.about_me
    return render_template('edit_profile.html',form=form)

#这是管理员修改用户资料的路由和视图
@main.route('/edit_profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    '''这是管理员修改用户资料的视图'''
    user=User.query.get_or_404(id)
    form=EditProfileAdminForm(user)
    if form.validate_on_submit():
        user.email=form.email.data
        user.username=form.username.data
        user.confirmed=form.confirmed.data
        user.role=Role.query.get(form.role.data)
        user.name=form.name.data
        user.location=form.location.data
        user.about_me=form.about_me.data
        db.session.add(user)
        flash('用户资料修改成功')
        return redirect(url_for('main.user',username=user.username))

    form.email.data=user.email
    form.username.data=user.username
    form.confirmed.data=user.confirmed
    form.role.data=user.role_id
    form.name.data=user.name
    form.location.data=user.location
    form.about_me.data=user.about_me
    return render_template('edit_profile.html',user=user,form=form)

#这是每篇博客的独立页面的路由和视图
@main.route('/post/<int:id>',methods=['GET','POST'])
def post(id):
    '''
    这是博客独立页面的视图

    :参数 id:博客的id
    '''
    post=Post.query.get_or_404(id)
    form=CommentForm()
    if form.validate_on_submit():
        comment=Comment(body=form.body.data,author=current_user._get_current_object(),post=post)
        db.session.add(comment)
        flash('评论成功')
        return redirect(url_for('main.post',id=post.id))
    page=request.args.get('page',1,type=int)
    pagination=post.comments.order_by(Comment.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments=pagination.items
    return render_template('post.html',posts=[post],comments=comments,pagination=pagination,form=form)

#这是编辑博客的路由和视图
@main.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):
    '''
    这是编辑博客的视图

    :参数 id:博客的id
    '''
    post=Post.query.get_or_404(id)
    #只有博文的作者和管理员可以修改文章
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.body=form.body.data
        db.session.add(post)
        flash('您的博客已更新')
        return redirect(url_for('main.post',id=post.id))
    form.body.data=post.body
    return render_template('edit_post.html',form=form)

#这是关注别人的路由和视图
@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    '''
    这是关注别人的视图
    
    :参数 username:这是被关注者的用户名
    '''
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('您已经关注了TA')
        return redirect(url_for('main.user',username=username))
    current_user.follow(user)
    flash('您正在关注%s'%username)
    return redirect(url_for('main.user',username=username))

#下面是取消关注某个人的路由和视图
@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    '''
    这是取消关注某个人的视图

    :参数 username:要取关的那位用户的用户名'''
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash('您未关注该用户')
        return redirect(url_for('main.user',username=username))
    current_user.unfollow(user)
    flash('您已取消对%s的关注'%username)
    return redirect(url_for('main.user',username=username))

#下面是粉丝列表页的路由和视图
@main.route('/followers/<username>')
def followers(username):
    '''
    这是粉丝列表也的视图

    :参数 username:要查看的用户的用户名
    '''
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('main.index'))
    #因为一个人可能有很多粉丝，所以要做分页处理
    #如果没有获取到合适的页码，就默认加载第1页
    page=request.args.get('page',1,type=int)
    pagination=user.followers.paginate(page,per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],error_out=False)
    #粉丝列表
    follows=[{'user':item.follower,'timestamp':item.timestamp} for item in pagination.items]
    #因为要用分页宏，所以这里还要传回去一个endpoint参数
    #title参数是因为我们希望粉丝模板和关注的人模板通用
    return render_template('followers.html',user=user,title='Followers',endpoint='main.followers',pagination=pagination,follows=follows,cn_title='的粉丝')


#下面是关注列表页的路由和视图
@main.route('/followed_by/<username>')
def followed_by(username):
    '''
    这是关注列表的视图

    :参数 username:这是要查看的这位用户的用户名
    '''
    user=User.query.filter_by(username=username)
    if user is None:
        flash('该用户不存在')
        return redirect(url_for('main.index'))
    page=request.args.get('page',1,type=int)
    pagination=user.followed.paginate(page,current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],error_out=False)
    follows=[{'user':item.followed,'timestamp':item.timestamp} for item in pagination.items]
    return render_template('followers.html',user=user,title='FOLLOWED BY',endpoint='main.followed_by',pagination=pagination,follows=follows,cn_title='的关注')

#这是在主页显示所有人的文章的路由和视图
@main.route('/all')
def show_all():
    '''这是在主页显示所有人的文章的视图'''
    resp=make_response(redirect(url_for('main.index')))
    #cookie只能在response对象中设置
    #这里设置的cookie的键是show_followed,值是空字符串,求布尔值的时候就会求成False
    #cookie的有效期单位是秒，这里设置30天的有效期
    resp.set_cookie('show_followed','',max_age=30*24*60*60)
    return resp

#这是在主页显示关注人的文章的路由和视图
@main.route('/followed')
def show_followed():
    '''这是在主页只显示关注人的文章的视图'''
    resp=make_response(redirect(url_for('main.index')))
    #这里cookie的值是字符串1，求布尔值会求为True
    resp.set_cookie('show_followed','1',max_age=30*24*60*60)
    return resp

#这是管理评论的路由和视图
@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    '''这是管理评论的视图'''
    page=request.args.get('page',1,type=int)
    pagination=Comment.query.order_by(Comment.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments=pagination.items
    return render_template('moderate.html',comments=comments,pagination=pagination)

#这是把评论恢复为显示状态的路由和视图
@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    '''这是协管员把评论恢复为显示状态的视图'''
    comment=Comment.query.get_or_404(id)
    comment.disabled=False
    db.session.add(comment)
    return redirect(url_for('main.moderate',page=request.args.get('page',1,type=int)))

#这是把评论屏蔽的路由和视图
@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    '''这是协管员屏蔽评论的视图'''
    comment=Comment.query.get_or_404(id)
    comment.disabled=True
    db.session.add(comment)
    return redirect(url_for('main.moderate',page=request.args.get('page',1,type=int)))

#下面是关闭服务器的路由，这主要是为了配合自动化测试
@main.route('/shutdown')
def server_shutdown():
    '''这是关闭服务器的视图'''
    #只允许在测试环境下使用
    if not current_app.testing:
        abort(404)
    shutdown=request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return ('正在关闭服务器')

#
@main.after_app_request
def after_request(response):
    '''
    这是在每次请求之后把缓慢的查询写入日记的方法

    :参数 response:每次请求获得的响应对象
    '''
    for query in get_debug_queries():
        if query.duration>=current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query:%s\nParameters:%s\nDuration:%fs\nContext:%s\n'%
                (query.statement,query.parameters,query.duration,query.context))
    return response
    