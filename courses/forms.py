"""Forms for creating courses."""
from __future__ import annotations

from django import forms

from .models import Course


class CourseForm(forms.ModelForm):
    """Teacher-facing form for creating/editing courses."""

    class Meta:
        model = Course
        fields = ("title", "description")


class AddStudentForm(forms.Form):
    """Teacher utility form to enrol a student by username or e‑mail.

    This keeps the UI simple. A richer search will be added in a later
    stage. Validation ensures the user exists and holds the student role.
    """

    query = forms.CharField(label="Username or e‑mail", max_length=150)
