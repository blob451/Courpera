"""
Baseline Django settings for Courpera (Stage 1 — scaffold).

Notes:
- This configuration is intentionally minimal to keep the initial
  scaffold straightforward. A settings split (base/dev/prod), REST, and
  Channels configuration follow in Stage 2.
- Canadian English is used for comments and docstrings.
"""
from pathlib import Path


# Base directory of the project (repository root)
BASE_DIR = Path(__file__).resolve().parent.parent


# Security
# CAUTION: This key is for local development only. Production configuration
# will provide a secret via environment variables in a later stage.
SECRET_KEY = "dev-insecure-key-change-me"

DEBUG = True  # Development default
ALLOWED_HOSTS: list[str] = []


# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local apps (only 'ui' is wired in Stage 1)
    "ui",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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

