import os
from .base import *

DEBUG = False

# استبدل USERNAME باسم مستخدمك الفعلي على PythonAnywhere
# (نفس الاسم الظاهر في الرابط: https://www.pythonanywhere.com/user/USERNAME/)
ALLOWED_HOSTS = ['USERNAME.pythonanywhere.com']

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-pythonanywhere-demo-key-change-me')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# PythonAnywhere (الخطة المجانية) تشغّل عملية واحدة فقط عبر WSGI، بلا خدمة
# منفصلة للواجهة — فتُخدَّم واجهة React المبنية (frontend/dist) من نفس
# الأصل، تمامًا كما في إعداد Replit.
SERVE_FRONTEND = True
FRONTEND_DIST = BASE_DIR.parent / 'frontend' / 'dist'

TEMPLATES[0]['DIRS'] = [FRONTEND_DIST]

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_ROOT = FRONTEND_DIST

CSRF_TRUSTED_ORIGINS = ['https://USERNAME.pythonanywhere.com']
