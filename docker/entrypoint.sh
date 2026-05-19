#!/bin/sh
set -e
cd /app/backend
python manage.py migrate --noinput
exec gunicorn --bind ":${PORT:-8080}" --workers 1 --threads 8 core.wsgi:application
