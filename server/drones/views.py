from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from accounts.auth import token_required
from .models import DroneDoc


def doc_dict(d):
    return {
        'id': d.id,
        'title': d.title,
        'model_name': d.model_name,
        'category': d.category,
        'category_label': d.get_category_display(),
        'tags': d.tags,
        'content': d.content,
        'created_at': d.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    }


def body_json(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return {}


@require_GET
@token_required
def doc_list(request):
    keyword = request.GET.get('keyword', '').strip()
    category = request.GET.get('category', '').strip()
    qs = DroneDoc.objects.all()
    if keyword:
        qs = qs.filter(
            Q(title__icontains=keyword)
            | Q(model_name__icontains=keyword)
            | Q(content__icontains=keyword)
            | Q(tags__icontains=keyword)
        )
    if category:
        qs = qs.filter(category=category)
    page = max(int(request.GET.get('page', 1)), 1)
    size = min(max(int(request.GET.get('size', 12)), 1), 50)
    total = qs.count()
    items = qs[(page - 1) * size: page * size]
    return JsonResponse({'code': 0, 'data': {'total': total, 'items': [doc_dict(d) for d in items]}})


@require_GET
@token_required
def doc_detail(request, pk):
    try:
        d = DroneDoc.objects.get(pk=pk)
    except DroneDoc.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '文档不存在'}, status=404)
    return JsonResponse({'code': 0, 'data': doc_dict(d)})


@csrf_exempt
@require_http_methods(['POST'])
@token_required
def doc_create(request):
    data = body_json(request)
    title = (data.get('title') or '').strip()
    if not title:
        return JsonResponse({'code': 400, 'message': '标题不能为空'}, status=400)
    doc = DroneDoc.objects.create(
        title=title,
        model_name=data.get('model_name', ''),
        category=data.get('category', 'faq'),
        tags=data.get('tags', ''),
        content=data.get('content', ''),
    )
    return JsonResponse({'code': 0, 'data': doc_dict(doc)})


@csrf_exempt
@require_http_methods(['PUT', 'DELETE'])
@token_required
def doc_update(request, pk):
    try:
        doc = DroneDoc.objects.get(pk=pk)
    except DroneDoc.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '文档不存在'}, status=404)

    if request.method == 'DELETE':
        doc.delete()
        return JsonResponse({'code': 0, 'message': '已删除'})

    data = body_json(request)
    for field in ['title', 'model_name', 'category', 'tags', 'content']:
        if field in data:
            setattr(doc, field, data[field])
    doc.save()
    return JsonResponse({'code': 0, 'data': doc_dict(doc)})


@require_GET
@token_required
def categories(request):
    cats = [{'value': k, 'label': v} for k, v in DroneDoc.CATEGORY_CHOICES]
    return JsonResponse({'code': 0, 'data': cats})
