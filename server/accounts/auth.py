from functools import wraps
from django.http import JsonResponse
from .models import AppUser


def get_user_from_request(request):
    token = request.headers.get('Authorization', '').replace('Token ', '').strip()
    if not token:
        token = request.GET.get('token', '').strip()
    if not token:
        return None
    return AppUser.objects.filter(api_token=token, is_active=True).first()


def token_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'code': 401, 'message': '请先登录或Token已失效'}, status=401)
        request.app_user = user
        return view_func(request, *args, **kwargs)
    return wrapper
