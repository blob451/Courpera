from django.urls import path

from .views import (
    CourperaLoginView,
    CourperaLogoutView,
    register,
    home,
    home_teacher,
    home_student,
    profile_edit,
    search_users,
    avatar_proxy,
)

app_name = "accounts"

urlpatterns = [
    path("login/", CourperaLoginView.as_view(), name="login"),
    path("logout/", CourperaLogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
    path("home/", home, name="home"),
    path("home/teacher/", home_teacher, name="home-teacher"),
    path("home/student/", home_student, name="home-student"),
    path("profile/", profile_edit, name="profile"),
    path("search/", search_users, name="search"),
    path("avatar/<int:user_id>/<int:size>/", avatar_proxy, name="avatar-proxy"),
]
