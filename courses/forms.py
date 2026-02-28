"""Forms for creating courses."""
from __future__ import annotations

from django import forms

from .models import Course
from django import forms


class CourseForm(forms.ModelForm):
    """Teacher-facing form for creating/editing courses."""

    class Meta:
        model = Course
        fields = ("title", "description")


class SyllabusForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("syllabus", "outcomes")
        widgets = {
            "syllabus": forms.Textarea(attrs={"rows": 8, "placeholder": "One item per line"}),
            "outcomes": forms.Textarea(attrs={"rows": 6, "placeholder": "One outcome per line"}),
        }


class AddStudentForm(forms.Form):
    """Teacher utility form to enrol a student by username, e-mail, or Student ID.

    This keeps the UI simple.
    """

    query = forms.CharField(label="Username, e-mail, or Student ID", max_length=150)
