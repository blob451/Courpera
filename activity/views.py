from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from accounts.decorators import role_required
from accounts.models import Role
from .forms import StatusForm


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

