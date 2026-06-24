import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
from accounts.auth import token_required
from .chroma_engine import ChromaEngine
from .weather_tool import weather_agent
from .models import ChatRecord


def body_json(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return {}


@csrf_exempt
@require_http_methods(['POST'])
@token_required
def ask(request):
    data = body_json(request)
    question = (data.get('question') or '').strip()
    if len(question) < 2:
        return JsonResponse({'code': 400, 'message': '请输入有效问题'}, status=400)
    try:
        engine = ChromaEngine()
        answer = engine.query(question)
    except RuntimeError as exc:
        return JsonResponse({'code': 503, 'message': str(exc)}, status=503)
    except Exception as exc:
        return JsonResponse({'code': 500, 'message': f'问答失败：{exc}'}, status=500)
    record = ChatRecord.objects.create(
        user=request.app_user,
        question=question,
        answer=answer,
        context='Chroma RAG',
    )
    return JsonResponse({'code': 0, 'data': {'id': record.id, 'question': question, 'answer': answer}})


@csrf_exempt
@require_http_methods(['POST'])
@token_required
def ask_stream(request):
    data = body_json(request)
    question = (data.get('question') or '').strip()
    if len(question) < 2:
        return JsonResponse({'code': 400, 'message': '请输入有效问题'}, status=400)

    user = request.app_user

    def stream_answer():
        answer_parts = []
        try:
            engine = ChromaEngine()
            for chunk in engine.query_stream(question):
                answer_parts.append(chunk)
                yield chunk.encode('utf-8')
        except RuntimeError as exc:
            message = f'\n\n[生成失败] {exc}'
            answer_parts.append(message)
            yield message.encode('utf-8')
        except Exception as exc:
            message = f'\n\n[生成失败] 问答失败：{exc}'
            answer_parts.append(message)
            yield message.encode('utf-8')
        finally:
            answer = ''.join(answer_parts).strip()
            if answer:
                ChatRecord.objects.create(
                    user=user,
                    question=question,
                    answer=answer,
                    context='Chroma RAG Stream',
                )

    response = StreamingHttpResponse(stream_answer(), content_type='text/plain; charset=utf-8')
    response['Cache-Control'] = 'no-cache'
    response['Content-Encoding'] = 'identity'
    response['X-Accel-Buffering'] = 'no'
    return response


@csrf_exempt
@require_http_methods(['POST'])
@token_required
def weather_ask(request):
    data = body_json(request)
    question = (data.get('question') or '').strip()
    if len(question) < 2:
        return JsonResponse({'code': 400, 'message': '请输入有效问题'}, status=400)
    try:
        answer = weather_agent(question)
    except RuntimeError as exc:
        return JsonResponse({'code': 503, 'message': str(exc)}, status=503)
    except Exception as exc:
        return JsonResponse({'code': 500, 'message': f'天气查询失败：{exc}'}, status=500)
    record = ChatRecord.objects.create(
        user=request.app_user,
        question=question,
        answer=answer,
        context='Weather Agent',
    )
    return JsonResponse({'code': 0, 'data': {'id': record.id, 'question': question, 'answer': answer}})


@require_GET
@token_required
def history(request):
    records = ChatRecord.objects.filter(user=request.app_user)[:30]
    return JsonResponse({'code': 0, 'data': [{
        'id': r.id,
        'question': r.question,
        'answer': r.answer,
        'context': r.context,
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    } for r in records]})


@csrf_exempt
@require_http_methods(['POST'])
@token_required
def build_index(request):
    try:
        engine = ChromaEngine()
        ok, msg = engine.build_index()
    except Exception as exc:
        return JsonResponse({'code': 500, 'message': f'索引构建失败：{exc}'}, status=500)
    code = 0 if ok else 500
    return JsonResponse({'code': code, 'message': msg}, status=200 if ok else 500)


@require_GET
@token_required
def search_preview(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'code': 400, 'message': '请提供查询词'}, status=400)
    try:
        engine = ChromaEngine()
        results = engine.search(q, n_results=3)
    except Exception as exc:
        return JsonResponse({'code': 500, 'message': str(exc)}, status=500)
    return JsonResponse({'code': 0, 'data': [
        {'title': r['meta'].get('title', ''), 'score': round(r['score'], 4), 'snippet': r['text'][:200]}
        for r in results
    ]})
