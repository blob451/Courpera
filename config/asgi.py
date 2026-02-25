"""ASGI entrypoint for Courpera.

This allows running under ASGI servers (e.g., Daphne/Uvicorn). WebSockets
and Channels configuration will be introduced in a later stage.
"""
import os
from django.core.asgi import get_asgi_application

# Default to development settings for local runs; override in deployment.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_asgi_application()
