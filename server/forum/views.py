import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
from accounts.auth import token_required
from .models import Post, Comment, PostLike


def body_json(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return {}


def post_dict(post, user=None):
    liked = False
    if user:
        liked = PostLike.objects.filter(post=post, user=user).exists()
    return {
        'id': post.id,
        'title': post.title,
        'category': post.category,
        'category_label': post.get_category_display(),
        'content': post.content,
        'author_id': post.author_id,
        'author_name': post.author.nickname or post.author.username,
        'view_count': post.view_count,
        'like_count': post.like_count,
        'comment_count': post.comments.count(),
        'liked': liked,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    }


def comment_dict(c):
    return {
        'id': c.id,
        'content': c.content,
        'author_id': c.author_id,
        'author_name': c.author.nickname or c.author.username,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    }


@require_GET
@token_required
def post_list(request):
    category = request.GET.get('category', '').strip()
    qs = Post.objects.select_related('author').all()
    if category:
        qs = qs.filter(category=category)
    page = max(int(request.GET.get('page', 1)), 1)
    size = min(max(int(request.GET.get('size', 20)), 1), 50)
    total = qs.count()
    items = qs[(page - 1) * size: page * size]
    return JsonResponse({'code': 0, 'data': {
        'total': total,
        'items': [post_dict(p, request.app_user) for p in items],
    }})


@require_GET
@token_required
def post_detail(request, pk):
    try:
        post = Post.objects.select_related('author').get(pk=pk)
    except Post.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '帖子不存在'}, status=404)
    Post.objects.filter(pk=pk).update(view_count=post.view_count + 1)
    post.refresh_from_db()
    comments = Comment.objects.filter(post=post).select_related('author')
    return JsonResponse({'code': 0, 'data': {
        'post': post_dict(post, request.app_user),
        'comments': [comment_dict(c) for c in comments],
    }})


@csrf_exempt
@require_http_methods(['POST'])
@token_required
def post_create(request):
    data = body_json(request)
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    if not title or not content:
        return JsonResponse({'code': 400, 'message': '标题和内容不能为空'}, status=400)
    post = Post.objects.create(
        author=request.app_user,
        title=title,
        category=data.get('category', 'qa'),
        content=content,
    )
    return JsonResponse({'code': 0, 'data': post_dict(post, request.app_user)})


@csrf_exempt
@require_http_methods(['PUT', 'DELETE'])
@token_required
def post_update(request, pk):
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '帖子不存在'}, status=404)
    if post.author_id != request.app_user.id:
        return JsonResponse({'code': 403, 'message': '无权操作'}, status=403)
    if request.method == 'DELETE':
        post.delete()
        return JsonResponse({'code': 0, 'message': '已删除'})
    data = body_json(request)
    for field in ['title', 'category', 'content']:
        if field in data:
            setattr(post, field, data[field])
    post.save()
    return JsonResponse({'code': 0, 'data': post_dict(post, request.app_user)})


@csrf_exempt
@require_http_methods(['POST'])
@token_required
def comment_create(request, pk):
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '帖子不存在'}, status=404)
    data = body_json(request)
    content = (data.get('content') or '').strip()
    if not content:
        return JsonResponse({'code': 400, 'message': '评论内容不能为空'}, status=400)
    comment = Comment.objects.create(post=post, author=request.app_user, content=content)
    return JsonResponse({'code': 0, 'data': comment_dict(comment)})


@csrf_exempt
@require_http_methods(['POST'])
@token_required
def post_like(request, pk):
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '帖子不存在'}, status=404)
    obj, created = PostLike.objects.get_or_create(post=post, user=request.app_user)
    if created:
        Post.objects.filter(pk=pk).update(like_count=post.like_count + 1)
        liked = True
    else:
        obj.delete()
        Post.objects.filter(pk=pk).update(like_count=max(post.like_count - 1, 0))
        liked = False
    post.refresh_from_db()
    return JsonResponse({'code': 0, 'data': {'liked': liked, 'like_count': post.like_count}})


@require_GET
@token_required
def categories(request):
    cats = [{'value': k, 'label': v} for k, v in Post.CATEGORY_CHOICES]
    return JsonResponse({'code': 0, 'data': cats})
