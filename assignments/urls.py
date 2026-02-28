from django.urls import path

from .views import (
    course_assignments,
    assignment_create,
    assignment_delete,
    quiz_manage,
    assignment_manage,
    assignment_take,
    assignment_submit,
    attempt_feedback,
    assignment_attempts,
    attempt_grade,
)

app_name = "assignments"

urlpatterns = [
    path("course/<int:course_id>/", course_assignments, name="course"),
    path("course/<int:course_id>/create/", assignment_create, name="create"),
    path("<int:pk>/delete/", assignment_delete, name="delete"),
    path("<int:pk>/quiz/", quiz_manage, name="quiz-manage"),
    path("<int:pk>/manage/", assignment_manage, name="manage"),
    path("<int:pk>/take/", assignment_take, name="take"),
    path("<int:pk>/submit/", assignment_submit, name="submit"),
    path("attempt/<int:attempt_id>/feedback/", attempt_feedback, name="feedback"),
    path("<int:pk>/attempts/", assignment_attempts, name="attempts"),
    path("attempt/<int:attempt_id>/grade/", attempt_grade, name="attempt-grade"),
]
