from django.urls import path

from .views import (
    course_list,
    course_create,
    course_edit,
    course_detail,
    course_enrol,
    course_unenrol,
    course_remove_student,
    course_add_student,
)

app_name = "courses"

urlpatterns = [
    path("", course_list, name="list"),
    path("create/", course_create, name="create"),
    path("<int:pk>/", course_detail, name="detail"),
    path("<int:pk>/edit/", course_edit, name="edit"),
    path("<int:pk>/enrol/", course_enrol, name="enrol"),
    path("<int:pk>/unenrol/", course_unenrol, name="unenrol"),
    path("<int:pk>/remove/<int:user_id>/", course_remove_student, name="remove"),
    path("<int:pk>/add-student/", course_add_student, name="add-student"),
]
