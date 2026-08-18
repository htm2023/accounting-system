import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['*']

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-replit-demo-key-change-me')

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

# Replit يشغّل عملية واحدة فقط، فتخدم Django واجهة React المبنية
# (frontend/dist) من نفس الأصل بدل نشرها كخدمة منفصلة كما على Render.
SERVE_FRONTEND = True
FRONTEND_DIST = BASE_DIR.parent / 'frontend' / 'dist'

TEMPLATES[0]['DIRS'] = [FRONTEND_DIST]

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_ROOT = FRONTEND_DIST
