import json
import secrets
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import AppUser
from .auth import token_required


def body_json(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return {}


def user_payload(user):
    return {
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'email': user.email,
        'bio': user.bio,
        'phone': user.phone,
        'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
    }

@csrf_exempt
@require_http_methods(['POST'])
def register(request):
    data = body_json(request)
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if len(username) < 3 or len(password) < 6:
        return JsonResponse({'code': 400, 'message': '用户名至少3位，密码至少6位'}, status=400)
    if AppUser.objects.filter(username=username).exists():
        return JsonResponse({'code': 400, 'message': '用户名已存在'}, status=400)
    user = AppUser.objects.create_user(
        username=username,
        password=password,
        email=data.get('email', ''),
        nickname=data.get('nickname', username),
    )
    return JsonResponse({'code': 0, 'message': '注册成功', 'data': user_payload(user)})

@csrf_exempt
@require_http_methods(['POST'])
def login(request):
    data = body_json(request)
    user = authenticate(username=data.get('username', ''), password=data.get('password', ''))
    if not user:
        return JsonResponse({'code': 400, 'message': '用户名或密码错误'}, status=400)
    token = secrets.token_hex(32)
    user.api_token = token
    user.save(update_fields=['api_token'])
    return JsonResponse({'code': 0, 'message': '登录成功', 'data': {'token': token, 'user': user_payload(user)}})

@csrf_exempt
@require_http_methods(['POST'])
@token_required
def logout(request):
    request.app_user.api_token = ''
    request.app_user.save(update_fields=['api_token'])
    return JsonResponse({'code': 0, 'message': '已退出登录'})

@csrf_exempt
@require_http_methods(['GET', 'PUT'])
@token_required
def profile(request):
    user = request.app_user
    if request.method == 'GET':
        return JsonResponse({'code': 0, 'data': user_payload(user)})
    data = body_json(request)
    for field in ['nickname', 'email', 'bio', 'phone']:
        if field in data:
            setattr(user, field, data.get(field) or '')
    if data.get('password'):
        if len(data['password']) < 6:
            return JsonResponse({'code': 400, 'message': '密码至少6位'}, status=400)
        user.set_password(data['password'])
    user.save()
    return JsonResponse({'code': 0, 'message': '资料已更新', 'data': user_payload(user)})
