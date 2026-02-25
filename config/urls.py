"""URL routing for Courpera (Stage 1 — scaffold).

Defines admin and the base UI index route. API and documentation routes
will be added in subsequent stages.
"""
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("ui.urls")),  # public index
]

