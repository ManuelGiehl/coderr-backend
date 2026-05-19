FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings
ENV PORT=8080

WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend .

# Create DB schema at image build time (Cloud Run startup must not block on migrate)
ENV SECRET_KEY=build-time-only-replaced-at-runtime
ENV DEBUG=False
ENV SQLITE_PATH=/app/backend/db.sqlite3
RUN python manage.py migrate --noinput

# Only start Gunicorn at runtime (fast listen on :8080 for Cloud Run health check)
CMD ["/bin/sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 8 core.wsgi:application"]
