from django.urls import path
from .views import post_status

app_name = "activity"

urlpatterns = [
    path("status/", post_status, name="post-status"),
]

