import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.auth import token_required

from .scoring import score_detections
from .pcb_defect_config import PCB_DEFECT_LABEL_CN, PCB_DEFECT_DEDUCT, PCB_DEFECT_SUGGESTIONS
from .yolo_service import SolderYoloService, YoloServiceError


ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


def _media_url(path):
    relative_path = Path(path).relative_to(settings.MEDIA_ROOT)
    return settings.MEDIA_URL + str(relative_path).replace('\\', '/')


def _save_upload(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError('仅支持 jpg、jpeg、png、bmp、webp 图片格式')

    upload_dir = Path(settings.MEDIA_ROOT) / 'soldering' / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f'{uuid.uuid4().hex}{suffix}'
    storage = FileSystemStorage(location=str(upload_dir))
    saved_name = storage.save(filename, uploaded_file)
    return upload_dir / saved_name


def _save_annotated(result):
    if result is None:
        return ''

    annotated_dir = Path(settings.MEDIA_ROOT) / 'soldering' / 'annotated'
    annotated_dir.mkdir(parents=True, exist_ok=True)
    output_path = annotated_dir / f'{uuid.uuid4().hex}.jpg'

    try:
        from PIL import Image
        annotated = result.plot(pil=True)
        if hasattr(annotated, 'save'):
            annotated.save(output_path, quality=92)
        else:
            Image.fromarray(annotated).save(output_path, quality=92)
    except Exception:
        return ''

    return _media_url(output_path)


@csrf_exempt
@require_http_methods(['POST'])
@token_required
def inspect(request):
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'code': 400, 'message': '请上传待检测图片'}, status=400)

    try:
        image_path = _save_upload(uploaded_file)
    except ValueError as exc:
        return JsonResponse({'code': 400, 'message': str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({'code': 500, 'message': f'图片保存失败：{exc}'}, status=500)

    try:
        detections, result = SolderYoloService.predict(image_path)
        actual_device = SolderYoloService.resolve_device()
        scored = score_detections(detections)
        annotated_image_url = _save_annotated(result)
    except YoloServiceError as exc:
        return JsonResponse({'code': 503, 'message': str(exc)}, status=503)
    except Exception as exc:
        return JsonResponse({'code': 500, 'message': f'焊点检测失败：{exc}'}, status=500)

    return JsonResponse({
        'code': 0,
        'data': {
            **scored,
            'image_url': _media_url(image_path),
            'annotated_image_url': annotated_image_url,
            'model': {
                'weights': Path(settings.SOLDER_YOLO_WEIGHTS).name,
                'device': actual_device,
                'confidence': settings.SOLDER_YOLO_CONF,
                'imgsz': settings.SOLDER_YOLO_IMGSZ,
            },
        },
    })


@csrf_exempt
@require_http_methods(['POST'])
@token_required
def inspect_pcb(request):
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'code': 400, 'message': '请上传待检测图片'}, status=400)

    try:
        image_path = _save_upload(uploaded_file)
    except ValueError as exc:
        return JsonResponse({'code': 400, 'message': str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({'code': 500, 'message': f'图片保存失败：{exc}'}, status=500)

    try:
        detections, result = SolderYoloService.predict(image_path, weights=settings.PCB_DEFECT_YOLO_WEIGHTS)
        actual_device = SolderYoloService.resolve_device()
        detections_out = []
        total_deduct = 0
        for item in detections:
            class_name = item['class_name']
            mapped = PCB_DEFECT_LABEL_CN.get(class_name, class_name)
            deduct = PCB_DEFECT_DEDUCT.get(class_name, 0)
            total_deduct += deduct
            detections_out.append({
                **item,
                'class_name': class_name,
                'label': mapped,
                'deduct': deduct,
                'suggestion': PCB_DEFECT_SUGGESTIONS.get(class_name, ''),
            })
        score = max(0, 100 - total_deduct)
        if score >= 90:
            grade = '优秀'
        elif score >= 80:
            grade = '良好'
        elif score >= 60:
            grade = '合格'
        else:
            grade = '不合格'
        if detections_out:
            summary = '检测到' + str(len(detections_out)) + '处PCB缺陷：' + '、'.join(
                f"{item['label']}1处" for item in detections_out
            ) + '。'
        else:
            summary = '未检测到PCB缺陷，建议结合人工复核确认。'
        suggestions = [item['suggestion'] for item in detections_out if item['suggestion']]
        if not suggestions:
            suggestions = ['请保持标准光照和清晰俯拍，必要时由教师结合原图进行人工复核。']
        annotated_image_url = _save_annotated(result)
    except YoloServiceError as exc:
        return JsonResponse({'code': 503, 'message': str(exc)}, status=503)
    except Exception as exc:
        return JsonResponse({'code': 500, 'message': f'PCB缺陷检测失败：{exc}'}, status=500)

    return JsonResponse({
        'code': 0,
        'data': {
            'score': score,
            'grade': grade,
            'summary': summary,
            'suggestions': suggestions,
            'total_deduct': total_deduct,
            'detections': detections_out,
            'image_url': _media_url(image_path),
            'annotated_image_url': annotated_image_url,
            'model': {
                'weights': Path(settings.PCB_DEFECT_YOLO_WEIGHTS).name,
                'device': actual_device,
                'confidence': settings.SOLDER_YOLO_CONF,
                'imgsz': settings.SOLDER_YOLO_IMGSZ,
            },
        },
    })
