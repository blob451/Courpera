"""Accounts models: user profile and roles.

Defines a `UserProfile` associated one-to-one with Django's `User`,
capturing the role (student/teacher) and optional contact fields. The
profile is created automatically on user creation.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class Role(models.TextChoices):
    """Platform roles used for simple role-based guards.

    Additional roles can be introduced later; this keeps the stage small
    and focused on the minimum required by the brief.
    """

    STUDENT = "student", "Student"
    TEACHER = "teacher", "Teacher"


class UserProfile(models.Model):
    """Profile linked to a Django auth user.

    - `role`: soft authorisation gate for views and pages
    - Contact fields are optional and can be extended later
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT)

    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    student_number = models.CharField(max_length=50, blank=True)

    # Placeholder for avatars; an external avatar URL or hash can be stored later
    avatar_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover (string repr convenience)
        return f"Profile<{self.user.username}:{self.role}>"

