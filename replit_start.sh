#!/usr/bin/env bash
set -e

export DJANGO_SETTINGS_MODULE=config.settings.replit

cd backend
pip3 install -r requirements.txt

cd ../frontend
npm install
VITE_API_URL=/api npm run build

cd ../backend
python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000
