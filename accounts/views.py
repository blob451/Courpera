"""Accounts views: registration, profile edit, and role home pages."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.db.models import Q
from django.contrib.auth.models import User
from django.urls import reverse

from .decorators import role_required
from .forms import RegistrationForm, ProfileForm
from .models import Role
from activity.forms import StatusForm
from activity.models import Status


class CourperaLoginView(LoginView):
    template_name = "registration/login.html"


class CourperaLogoutView(LogoutView):
    next_page = "/"
    # Allow GET to support direct navigation to the logout URL without 405.
    http_method_names = ["get", "post", "head", "options"]
    # Convenience: accept GET as well to avoid 405 when users follow a link.
    # In stricter deployments, prefer POST-only logout.
    def get(self, request, *args, **kwargs):  # pragma: no cover
        return self.post(request, *args, **kwargs)


def register(request: HttpRequest) -> HttpResponse:
    """Register a new user and pick an initial role.

    On success, the user is logged in and redirected to the role-aware
    home view which then routes to student/teacher pages.
    """
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to Courpera!")
            return redirect("accounts:home")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def home(request: HttpRequest) -> HttpResponse:
    """Dispatch to a role-specific home page."""
    role = getattr(getattr(request.user, "profile", None), "role", None)
    if role == Role.TEACHER:
        return redirect("accounts:home-teacher")
    return redirect("accounts:home-student")


@login_required
@role_required(Role.TEACHER)
def home_teacher(request: HttpRequest) -> HttpResponse:
    return render(request, "accounts/home_teacher.html")


@login_required
@role_required(Role.STUDENT)
def home_student(request: HttpRequest) -> HttpResponse:
    updates = Status.objects.filter(user=request.user)[:20]
    form = StatusForm()
    return render(request, "accounts/home_student.html", {"updates": updates, "status_form": form})


@login_required
@role_required(Role.TEACHER)
def search_users(request: HttpRequest) -> HttpResponse:
    """Teacher-only user search by username or e-mail (partial, case-insensitive)."""
    q = (request.GET.get("q") or "").strip()
    results = []
    if q:
        results = (
            User.objects.select_related("profile")
            .filter(Q(username__icontains=q) | Q(email__icontains=q))
            .order_by("username")[:50]
        )
    return render(request, "accounts/search.html", {"q": q, "results": results})


@login_required
def profile_edit(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:home")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "accounts/profile.html", {"form": form})
