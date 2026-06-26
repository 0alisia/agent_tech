import threading
from pathlib import Path
import sys

from django.conf import settings


PROJECT_DIR = Path(__file__).resolve().parents[1]
VENDOR_ULTRALYTICS = PROJECT_DIR / 'vendor_ultralytics'
for path in (str(VENDOR_ULTRALYTICS), str(PROJECT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)


class YoloServiceError(RuntimeError):
    pass


class SolderYoloService:
    _model = None
    _models = {}
    _lock = threading.Lock()

    @classmethod
    def get_model(cls, weights=None):
        weights_key = str(weights or settings.SOLDER_YOLO_WEIGHTS).strip()
        if weights_key in cls._models:
            return cls._models[weights_key]

        if weights is None and cls._model is not None:
            return cls._model

        with cls._lock:
            if weights_key in cls._models:
                return cls._models[weights_key]
            if weights is None and cls._model is not None:
                return cls._model

            weights = weights_key
            if not weights:
                raise YoloServiceError('未配置YOLO权重：SOLDER_YOLO_WEIGHTS为空')

            weights_path = Path(weights).expanduser()
            is_local_path = weights_path.is_absolute() or '/' in weights or '\\' in weights
            if is_local_path and not weights_path.exists():
                if weights_path.name == 'yolov8n.pt':
                    model_source = 'yolov8n.pt'
                else:
                    raise YoloServiceError(f'未找到YOLO权重文件：{weights_path}')
            else:
                model_source = str(weights_path) if is_local_path else weights


            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise YoloServiceError('当前环境未安装ultralytics，请先在drone-rag环境中安装。') from exc

            try:
                model = YOLO(model_source)
            except Exception as exc:
                raise YoloServiceError(f'YOLO模型加载失败：{exc}') from exc

            cls._models[weights_key] = model
            if weights_key == str(settings.SOLDER_YOLO_WEIGHTS).strip():
                cls._model = model

        return model

    @classmethod
    def predict(cls, image_path, weights=None):
        model = cls.get_model(weights)
        device = cls.resolve_device()
        try:
            results = model.predict(
                source=str(image_path),
                conf=settings.SOLDER_YOLO_CONF,
                imgsz=settings.SOLDER_YOLO_IMGSZ,
                device=device,
                verbose=False,
            )
        except Exception as exc:
            raise YoloServiceError(f'YOLO推理失败：{exc}') from exc

        if not results:
            return [], None

        result = results[0]
        detections = cls._parse_result(result)
        return detections, result

    @staticmethod
    def resolve_device():
        configured = str(settings.SOLDER_YOLO_DEVICE).strip().lower()
        if configured and configured != 'auto':
            return configured

        try:
            import torch
            return '0' if torch.cuda.is_available() else 'cpu'
        except Exception:
            return 'cpu'

    @staticmethod
    def _parse_result(result):
        detections = []
        names = result.names or {}
        boxes = getattr(result, 'boxes', None)
        if boxes is None:
            return detections

        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            class_name = str(names.get(class_id, class_id))
            detections.append({
                'class_id': class_id,
                'class_name': class_name,
                'confidence': round(confidence, 4),
                'box': {
                    'x1': round(float(xyxy[0]), 2),
                    'y1': round(float(xyxy[1]), 2),
                    'x2': round(float(xyxy[2]), 2),
                    'y2': round(float(xyxy[3]), 2),
                },
            })
        return detections
