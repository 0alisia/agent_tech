import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'drone-rag-secret-key-2024')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'accounts',
    'drones',
    'forum',
    'rag',
    'soldering',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dronekg.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'dronekg.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'accounts.AppUser'
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_ALL_ORIGINS = True

DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '')
DASHSCOPE_MODEL = os.getenv('DASHSCOPE_MODEL', 'qwen-plus')
DASHSCOPE_EMBEDDING_MODEL = os.getenv('DASHSCOPE_EMBEDDING_MODEL', 'text-embedding-v4')
DASHSCOPE_EMBEDDING_DIM = int(os.getenv('DASHSCOPE_EMBEDDING_DIM', '1024'))
HEFENG_API_KEY = os.getenv('HEFENG_API_KEY', '')
HEFENG_API_HOST = os.getenv('HEFENG_API_HOST', '')

CHROMA_PERSIST_DIR = str(BASE_DIR / 'chroma_storage')

SOLDER_YOLO_WEIGHTS = os.getenv(
    'SOLDER_YOLO_WEIGHTS',
    str(BASE_DIR / 'weights' / 'yolov8n.pt')
)
PCB_DEFECT_YOLO_WEIGHTS = os.getenv(
    'PCB_DEFECT_YOLO_WEIGHTS',
    str(BASE_DIR / 'weights' / 'pcb_defect_yolo11_best.pt')
)
SOLDER_YOLO_CONF = float(os.getenv('SOLDER_YOLO_CONF', '0.45'))
SOLDER_YOLO_IMGSZ = int(os.getenv('SOLDER_YOLO_IMGSZ', '960'))
SOLDER_YOLO_DEVICE = os.getenv('SOLDER_YOLO_DEVICE', 'auto')
