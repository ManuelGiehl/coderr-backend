FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings
ENV PORT=8080
ENV SQLITE_PATH=/tmp/db.sqlite3

WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend .

# Same pattern as revision 00003 (deploy worked); migrate then gunicorn on 0.0.0.0
CMD ["/bin/sh", "-c", "rm -f \"$SQLITE_PATH\" && python manage.py migrate --noinput && exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 8 core.wsgi:application"]
