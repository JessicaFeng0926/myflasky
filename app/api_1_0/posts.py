from . import api
from .decorators import permission_required
from ..models import Permission,Post
from flask import request,jsonify,g,url_for,current_app
from .. import db
from .errors import forbidden

@api.route('/posts/',methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    '''这是通过json创建新博客的视图'''
    post=Post.from_json(request.json)
    post.author=g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()),201,{'Location':url_for('api.get_post',id=post.id,_external=True)}

@api.route('/posts/<int:id>',methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
    '''这是更新现有的博客的方法'''
    post=Post.query.get_or_404(id)
    if g.current_user!=post.author and not g.current_user.can(Permission.ADMINISTER):
        return forbidden('Insufficient permissions')
    post.body=request.json.get('body',post.body)
    db.session.add(post)
    return jsonify(post.to_json())

@api.route('/posts/')
def get_posts():
    '''这是获取所有文章的视图'''
    page=request.args.get('page',1,type=int)
    pagination=Post.query.paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts=pagination.items
    prev=None
    if pagination.has_prev:
        prev=url_for('api.get_posts',page=pagination.prev_num,_external=True)
    next=None
    if pagination.has_next:
        next=url_for('api.get_posts',page=pagination.next_num,_external=True)
    return jsonify({
        'posts':[post.to_json() for post in posts],
        'prev':prev,
        'next':next,
        'count':pagination.total
    })

@api.route('posts/<int:id>')
def get_post(id):
    '''这是获取一篇博客的视图'''
    post=Post.query.get_or_404(id)
    return jsonify(post.to_json())
