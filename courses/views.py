"""Course list/detail and enrolment actions (Stage 5)."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import Role
from django.contrib.auth.models import User
from django.db.models import Q
from .forms import CourseForm, AddStudentForm
from .models import Course, Enrolment
from .models_feedback import Feedback
from .forms_feedback import FeedbackForm


def _is_enrolled(user, course: Course) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return Enrolment.objects.filter(course=course, student=user).exists()


def course_list(request: HttpRequest) -> HttpResponse:
    """Public course catalogue; actions vary by role."""
    courses = Course.objects.select_related("owner").all()
    enrolments = set()
    if request.user.is_authenticated:
        enrolments = set(Enrolment.objects.filter(student=request.user).values_list("course_id", flat=True))
    ctx = {"courses": courses, "enrolled_ids": enrolments, "role": getattr(getattr(request.user, "profile", None), "role", None)}
    return render(request, "courses/list.html", ctx)


@login_required
@role_required(Role.TEACHER)
def course_create(request: HttpRequest) -> HttpResponse:
    """Teacher-only course creation."""
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.owner = request.user
            course.save()
            messages.success(request, "Course created.")
            return redirect("courses:detail", pk=course.pk)
    else:
        form = CourseForm()
    return render(request, "courses/create.html", {"form": form})


@login_required
@role_required(Role.TEACHER)
def course_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Teacher-only edit of course title/description (owner only)."""
    course = get_object_or_404(Course, pk=pk)
    if not course.is_owner(request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated.")
            return redirect("courses:detail", pk=course.pk)
    else:
        form = CourseForm(instance=course)
    return render(request, "courses/create.html", {"form": form})


@login_required
def course_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Course detail restricted to owner or enrolled students."""
    course = get_object_or_404(Course.objects.select_related("owner"), pk=pk)
    owner_view = course.is_owner(request.user)
    is_enrolled = _is_enrolled(request.user, course)
    # Allow non-enrolled students to see a limited view (title, teacher, feedback list).
    limited_view = not (owner_view or is_enrolled)

    # For teachers, show roster; for students, show a concise message.
    roster = None
    add_form = None
    feedback_form = None
    if owner_view:
        roster = Enrolment.objects.filter(course=course).select_related("student").order_by("student__username")
        add_form = AddStudentForm()
    if is_enrolled:
        # Initialise form with existing feedback if present
        existing = Feedback.objects.filter(course=course, student=request.user).first()
        feedback_form = FeedbackForm(instance=existing)
    ctx = {
        "course": course,
        "owner_view": owner_view,
        "is_enrolled": is_enrolled,
        "limited_view": limited_view,
        "roster": roster,
        "add_form": add_form,
        "feedback_form": feedback_form,
        "feedback_list": Feedback.objects.filter(course=course).select_related("student"),
    }
    return render(request, "courses/detail.html", ctx)


@login_required
@role_required(Role.STUDENT)
def course_enrol(request: HttpRequest, pk: int) -> HttpResponse:
    """Enrol the current student into a course (idempotent)."""
    course = get_object_or_404(Course, pk=pk)
    if request.method == "POST":
        _, created = Enrolment.objects.get_or_create(course=course, student=request.user)
        if created:
            messages.success(request, "Enrolled in course.")
        return redirect("courses:detail", pk=course.pk)
    return redirect("courses:list")


@login_required
@role_required(Role.TEACHER)
def course_remove_student(request: HttpRequest, pk: int, user_id: int) -> HttpResponse:
    """Teacher removes a student from their course.

    Permission: only the course owner can remove students.
    """
    course = get_object_or_404(Course, pk=pk)
    if not course.is_owner(request.user):
        raise PermissionDenied
    if request.method == "POST":
        Enrolment.objects.filter(course=course, student_id=user_id).delete()
        messages.success(request, "Student removed from course.")
    return redirect("courses:detail", pk=course.pk)


@login_required
@role_required(Role.TEACHER)
def course_add_student(request: HttpRequest, pk: int) -> HttpResponse:
    """Teacher enrols a student by username or e‑mail (owner only), or searches.

    Behaviour:
    - If the submitted button named 'action' has value 'search', perform a
      partial match search on username/e‑mail and render the course detail
      with results.
    - Otherwise, attempt to enrol a single user identified by the query
      (exact username or e‑mail match), then redirect back to detail.
    """
    course = get_object_or_404(Course, pk=pk)
    if not course.is_owner(request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = AddStudentForm(request.POST)
        if form.is_valid():
            q = form.cleaned_data["query"].strip()
            action = request.POST.get("action", "enrol").lower()
            if action == "search":
                # Partial, case-insensitive match on username or e‑mail; student role only
                results = (
                    User.objects.select_related("profile")
                    .filter(Q(username__icontains=q) | Q(email__icontains=q))
                    .filter(profile__role=Role.STUDENT)
                    .order_by("username")[:20]
                )
                roster = (
                    Enrolment.objects.filter(course=course)
                    .select_related("student")
                    .order_by("student__username")
                )
                ctx = {
                    "course": course,
                    "owner_view": True,
                    "is_enrolled": False,
                    "roster": roster,
                    "add_form": form,
                    "search_results": results,
                    "searched": True,
                }
                return render(request, "courses/detail.html", ctx)
            # Enrol flow: exact match on username or e‑mail
            target = (
                User.objects.select_related("profile").filter(username__iexact=q).first()
                or User.objects.select_related("profile").filter(email__iexact=q).first()
            )
            if not target:
                messages.error(request, "No user found for that username or e‑mail.")
                return redirect("courses:detail", pk=course.pk)
            profile = getattr(target, "profile", None)
            if not profile or profile.role != Role.STUDENT:
                messages.error(request, "User is not a student.")
                return redirect("courses:detail", pk=course.pk)
            Enrolment.objects.get_or_create(course=course, student=target)
            messages.success(request, f"Enrolled {target.username}.")
    return redirect("courses:detail", pk=course.pk)


@login_required
@role_required(Role.STUDENT)
def course_unenrol(request: HttpRequest, pk: int) -> HttpResponse:
    """Student unenrols from a course (owner unaffected)."""
    course = get_object_or_404(Course, pk=pk)
    if request.method == "POST":
        Enrolment.objects.filter(course=course, student=request.user).delete()
        messages.success(request, "Unenrolled from course.")
    return redirect("courses:list")


@login_required
@role_required(Role.STUDENT)
def course_feedback(request: HttpRequest, pk: int) -> HttpResponse:
    """Create or update feedback for a course (student-only, enrolled)."""
    course = get_object_or_404(Course, pk=pk)
    if not Enrolment.objects.filter(course=course, student=request.user).exists():
        messages.error(request, "Please enrol before leaving feedback.")
        return redirect("courses:detail", pk=course.pk)
    if request.method == "POST":
        existing = Feedback.objects.filter(course=course, student=request.user).first()
        form = FeedbackForm(request.POST, instance=existing)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.course = course
            fb.student = request.user
            fb.save()
            messages.success(request, "Feedback saved.")
        else:
            messages.error(request, "Invalid feedback.")
    return redirect("courses:detail", pk=course.pk)
