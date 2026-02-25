"""Upload and management views for course materials."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect

from accounts.decorators import role_required
from accounts.models import Role
from courses.models import Course
from .forms import MaterialUploadForm
from .models import Material


@login_required
@role_required(Role.TEACHER)
def upload_for_course(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_owner(request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = MaterialUploadForm(request.POST, request.FILES)
        if form.is_valid():
            m = form.save(commit=False)
            m.course = course
            m.uploaded_by = request.user
            m.save()
            messages.success(request, "Material uploaded.")
        else:
            messages.error(request, "; ".join([str(e) for e in form.errors.get("file", [])]) or "Upload failed.")
    return redirect("courses:detail", pk=course.pk)


@login_required
@role_required(Role.TEACHER)
def delete_material(request: HttpRequest, pk: int) -> HttpResponse:
    m = get_object_or_404(Material.objects.select_related("course"), pk=pk)
    if not m.course.is_owner(request.user):
        raise PermissionDenied
    if request.method == "POST":
        course_id = m.course_id
        m.delete()
        messages.success(request, "Material deleted.")
        return redirect("courses:detail", pk=course_id)
    return redirect("courses:list")

