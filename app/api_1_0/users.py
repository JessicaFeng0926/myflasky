from ..models import User,Post
from flask import request,url_for,current_app,jsonify
from . import api

@api.route('users/<int:id>')
def get_user(id):
    '''这是获取一个用户的视图'''
    user=User.query.get_or_404(id)
    return jsonify(user.to_json())

@api.route('/users/<int:id>/posts/')
def get_user_posts(id):
    '''这是获取某位用户的全部博客的视图'''
    user=User.query.get_or_404(id)
    page=request.args.get('page',1,type=int)
    pagination=user.posts.order_by(Post.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts=pagination.items
    prev=None
    if pagination.has_prev:
        prev=url_for('api.get_user_posts',page=pagination.prev_num,id=id)
    next=None
    if pagination.has_next:
        next=url_for('api.get_user_posts',page=pagination.next_num,id=id)
    return jsonify({
        'posts':[post.to_json() for post in posts],
        'prev':prev,
        'next':next,
        'count':pagination.total
    })

@api.route('/users/<int:id>/timeline')
def get_user_followed_posts(id):
    '''这是获取用户的关注人的博客的视图'''
    user=User.query.get_or_404(id)
    page=request.args.get('page',1,type=int)
    pagination=user.followed_posts.order_by(Post.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts=pagination.items
    prev=None
    if pagination.has_prev:
        prev=url_for('api.get_user_followed_posts',id=id,page=pagination.prev_num)
    next=None
    if pagination.has_next:
        next=url_for('api.get_user_followed_posts',id=id,page=pagination.next_num)
    return jsonify({
        'posts':[post.to_json() for post in posts],
        'prev':prev,
        'next':next,
        'count':pagination.total
    })
