"""Accounts views: registration, profile edit, and role home pages."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse, Http404, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.db.models import Q
from django.contrib.auth.models import User
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.conf import settings
import hashlib
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError

from .decorators import role_required
from .forms import RegistrationForm, ProfileForm
from .models import Role
from activity.forms import StatusForm
from activity.models import Status


class CourperaLoginView(LoginView):
    template_name = "registration/login.html"

    def post(self, request: HttpRequest, *args, **kwargs):
        # Simple per-session login throttle: max 10 attempts/min to reduce brute force
        try:
            ts = request.session.get("login_ts", [])
            now = __import__("time").time()
            ts = [t for t in ts if now - t < 60]
            if len(ts) >= 10:
                messages.error(request, "Too many login attempts. Please wait a minute and try again.")
                return self.get(request, *args, **kwargs)
            ts.append(now)
            request.session["login_ts"] = ts
        except Exception:
            pass
        return super().post(request, *args, **kwargs)


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


@require_GET
def avatar_proxy(request: HttpRequest, user_id: int, size: int) -> HttpResponse:
    """Proxy DiceBear avatar as same-origin PNG to avoid ORB issues.

    Accepts deterministic query params but recomputes seed server-side.
    """
    try:
        size = int(size)
    except Exception:  # pragma: no cover
        return HttpResponseBadRequest("invalid size")
    if size < 16 or size > 256:
        return HttpResponseBadRequest("invalid size")

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:  # pragma: no cover - edge
        raise Http404("user not found") from exc

    # Compute deterministic seed
    seed_src = f"{getattr(user, 'pk', '0')}:{getattr(settings, 'AVATAR_SEED_SALT', 'courpera')}"
    seed = hashlib.sha256(seed_src.encode()).hexdigest()

    base = getattr(settings, "AVATAR_BASE_URL", "https://api.dicebear.com/7.x")
    style = getattr(settings, "AVATAR_STYLE", "initials")
    params = {
        "seed": seed,
        "size": size,
        "backgroundColor": "lightgray",
    }
    url = f"{base}/{style}/png?{urlencode(params)}"

    try:
        req = Request(url, headers={"User-Agent": "Courpera/1.0"})
        with urlopen(req, timeout=5) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "image/png")
    except (URLError, HTTPError):  # pragma: no cover - network
        # Fallback: transparent 1x1 PNG
        transparent_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc``\x00\x00\x00\x02\x00\x01E\x1d\xc2\x02\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        data = transparent_png
        ctype = "image/png"

    r = HttpResponse(data, content_type=ctype)
    r["Cache-Control"] = "public, max-age=86400"
    return r
