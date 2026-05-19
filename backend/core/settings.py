"""
Django settings for core project.

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path

from decouple import Config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# Project root (parent of backend/) – .env lives here
PROJECT_ROOT = BASE_DIR.parent
_env_file = PROJECT_ROOT / '.env'


def _cast_env_value(value, cast):
    """Cloud Run env vars are strings; bool('False') would wrongly be True."""
    if cast is bool:
        return value.strip().lower() in ('true', '1', 't', 'yes', 'on')
    if cast is not None:
        return cast(value)
    return value


class _EnvConfig:
    """Read settings from OS env (e.g. Cloud Run) when no .env file is present."""

    def __call__(self, key, default=None, cast=None):
        value = os.environ.get(key)
        if value is None:
            return default
        return _cast_env_value(value, cast)


config = Config(str(_env_file)) if _env_file.is_file() else _EnvConfig()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Comma-separated in .env; includes local dev + production API + frontend host
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default=(
        '127.0.0.1,localhost,testserver,'
        'apicoderr.manuelgiehl.com,coderr.manuelgiehl.com'
    ),
    cast=Csv(),
)

# HTTPS origins (Django 4+); needed e.g. for admin/forms behind HTTPS
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default=(
        'https://coderr.manuelgiehl.com,'
        'https://apicoderr.manuelgiehl.com'
    ),
    cast=Csv(),
)

# Reverse proxy (Ionos/nginx): set USE_X_FORWARDED_PROTO=True in .env on the server
if config('USE_X_FORWARDED_PROTO', default=False, cast=bool):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'auth_app',
    'base_info_app',
    'offers_app',
    'orders_app',
    'profiles_app',
    'reviews_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Media files (user uploads, e.g. offer images)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST framework: token auth for API
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

# CORS: dev = permissive; production = only the SPA origin(s)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = config(
        'CORS_ALLOWED_ORIGINS',
        default='https://coderr.manuelgiehl.com',
        cast=Csv(),
    )
