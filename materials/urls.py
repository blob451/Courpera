from django.urls import path

from .views import upload_for_course, delete_material

app_name = "materials"

urlpatterns = [
    path("course/<int:course_id>/upload/", upload_for_course, name="upload"),
    path("<int:pk>/delete/", delete_material, name="delete"),
]

