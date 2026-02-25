from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from accounts.decorators import role_required
from accounts.models import Role
from .forms import StatusForm
from .models import Status, Notification


@login_required
@role_required(Role.STUDENT)
def post_status(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = StatusForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.user = request.user
            s.save()
            messages.success(request, "Status posted.")
        else:
            messages.error(request, "Invalid status update.")
    return redirect("accounts:home-student")


@login_required
def notifications_recent(request: HttpRequest) -> JsonResponse:
    """Return recent notifications and unread count for the current user."""
    limit = 10
    try:
        limit = int(getattr(request, "GET", {}).get("limit", 10))
    except Exception:
        limit = 10
    qs = Notification.objects.filter(user=request.user).order_by("-created_at")
    unread = qs.filter(read=False).count()
    items = list(qs[:limit])
    data = [
        {
            "id": n.id,
            "type": n.type,
            "message": n.message,
            "created_at": n.created_at.isoformat(),
            "read": n.read,
        }
        for n in items
    ]
    return JsonResponse({"unread": unread, "results": data})


@login_required
def notifications_page(request: HttpRequest) -> HttpResponse:
    qs = Notification.objects.filter(user=request.user).order_by("-created_at")[:100]
    return render(request, "activity/notifications.html", {"notifications": qs})


@login_required
def notifications_mark_all_read(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        messages.success(request, "Notifications marked as read.")
    return redirect("activity:notifications-page")
