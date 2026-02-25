"""URL routing for Courpera (Stage 1 — scaffold).

Defines admin and the base UI index route. API and documentation routes
will be added in subsequent stages.
"""
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.conf import settings
from django.conf.urls.static import static


def _favicon(request):  # redirect to static SVG favicon to avoid 404s
    return HttpResponsePermanentRedirect("/static/favicon.svg")


urlpatterns = [
    path("favicon.ico", _favicon),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("courses/", include("courses.urls")),
    path("materials/", include("materials.urls")),
    path("activity/", include("activity.urls")),
    path("messaging/", include("messaging.urls")),
    path("", include("ui.urls")),  # public index
    # API schema and docs
    path("", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
