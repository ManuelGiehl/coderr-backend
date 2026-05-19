#!/bin/sh
set -e
cd /app/backend

# Cloud Run + SQLite: avoid a partial/old db.sqlite3 from uploads or failed migrates
rm -f db.sqlite3

echo "=== Running migrations ==="
python manage.py migrate --noinput --verbosity 2
python manage.py showmigrations

echo "=== Starting Gunicorn ==="
exec gunicorn --bind ":${PORT:-8080}" --workers 1 --threads 8 core.wsgi:application
