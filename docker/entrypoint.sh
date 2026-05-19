#!/bin/sh
set -e
cd /app/backend

# Cloud Run + SQLite: avoid a partial/old db.sqlite3 from uploads or failed migrates
rm -f db.sqlite3

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Starting Gunicorn on port ${PORT:-8080} ==="
exec gunicorn --bind ":${PORT:-8080}" --workers 1 --threads 8 core.wsgi:application
