"""Base Django settings for Courpera (Stage 2 — split + API docs).

This base layer is environment-agnostic. Development/production-specific
settings extend from this module in `dev.py` and `prod.py`.
"""
from pathlib import Path
import os


# Base directory of the project (repository root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Security (overridden in dev/prod)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-key-change-me")
DEBUG = False
ALLOWED_HOSTS: list[str] = []


# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps (API + docs)
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    # Local apps
    "ui",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise will be enabled in production; keep ordering stable now
    # "whitenoise.middleware.WhiteNoiseMiddleware",  # enabled in prod.py
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Global templates directory at the repository root
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# Database — SQLite-first as per project philosophy
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Internationalisation (Canadian English; Mountain Time zone for Calgary)
LANGUAGE_CODE = "en-ca"
TIME_ZONE = "America/Edmonton"
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
_static_dir = BASE_DIR / "static"
STATICFILES_DIRS = [_static_dir] if _static_dir.exists() else []


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework (minimal defaults; refined later)
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DATETIME_FORMAT": "iso-8601",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Courpera API",
    "DESCRIPTION": "REST API and OpenAPI documentation for Courpera.",
    "VERSION": "0.1.0",
    # Ensure /api/schema/ remains available (even when incomplete) for local/dev
    "DISABLE_ERRORS_AND_WARNINGS": True,
    "SERVE_INCLUDE_SCHEMA": True,
}


# Channels — configured later; keep a placeholder for local fallback
REDIS_URL = os.environ.get("REDIS_URL", "")
if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }
