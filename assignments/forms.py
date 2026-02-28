from __future__ import annotations

from django import forms
from django.utils import timezone

from .models import Assignment, QuizQuestion, QuizAnswerChoice, AssignmentType


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ("type", "title", "instructions", "available_from", "deadline", "attempts_allowed")
        widgets = {
            "instructions": forms.Textarea(attrs={"rows": 4}),
            # Use a local datetime input for better UX (browser-native picker)
            "deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "available_from": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure only the defined types are selectable and set a sensible default
        from .models import AssignmentType as _AT
        self.fields["type"].choices = list(_AT.choices)
        if not self.initial.get("type"):
            self.fields["type"].initial = _AT.QUIZ
        # Add client-side min attribute to date inputs (current local time)
        try:
            now = timezone.localtime(timezone.now(), timezone.get_current_timezone())
            now_str = now.strftime("%Y-%m-%dT%H:%M")
            if "available_from" in self.fields:
                self.fields["available_from"].widget.attrs.setdefault("min", now_str)
            if "deadline" in self.fields:
                self.fields["deadline"].widget.attrs.setdefault("min", now_str)
        except Exception:
            pass
        # Ensure initial deadline renders in the widget format if present
        if self.instance and self.instance.deadline:
            d = self.instance.deadline
            if timezone.is_aware(d):
                d = timezone.localtime(d, timezone.get_current_timezone())
            self.initial["deadline"] = d.strftime("%Y-%m-%dT%H:%M")
        if self.instance and getattr(self.instance, "available_from", None):
            a = self.instance.available_from
            if timezone.is_aware(a):
                a = timezone.localtime(a, timezone.get_current_timezone())
            self.initial["available_from"] = a.strftime("%Y-%m-%dT%H:%M")

    def clean_deadline(self):
        d = self.cleaned_data.get("deadline")
        # Allow empty; if present, convert to aware and enforce future
        if not d:
            return d
        if timezone.is_naive(d):
            d = timezone.make_aware(d, timezone.get_current_timezone())
        if d <= timezone.now():
            raise forms.ValidationError("Deadline must be in the future.")
        return d

    def clean_available_from(self):
        a = self.cleaned_data.get("available_from")
        if not a:
            return a
        if timezone.is_naive(a):
            a = timezone.make_aware(a, timezone.get_current_timezone())
        return a

    def clean(self):
        cleaned = super().clean()
        a = cleaned.get("available_from")
        d = cleaned.get("deadline")
        if a and d and a >= d:
            self.add_error("available_from", "Availability must be before the deadline.")
        return cleaned

    def clean_attempts_allowed(self):
        val = self.cleaned_data.get("attempts_allowed")
        try:
            val = int(val or 0)
        except Exception:
            raise forms.ValidationError("Invalid attempts value.")
        if val < 1:
            raise forms.ValidationError("Attempts must be at least 1.")
        # If editing an existing assignment, prevent lowering below used attempts
        if getattr(self, 'instance', None) and getattr(self.instance, 'pk', None):
            try:
                from .models import Attempt  # local import to avoid cycles
                used = Attempt.objects.filter(assignment=self.instance).count()
                if val < used:
                    raise forms.ValidationError(f"Cannot set attempts below attempts already used ({used}).")
            except Exception:
                pass
        return val


class QuizQuestionForm(forms.ModelForm):
    class Meta:
        model = QuizQuestion
        fields = ("text",)
        widgets = {"text": forms.Textarea(attrs={"rows": 2})}


class QuizAnswerChoiceForm(forms.ModelForm):
    class Meta:
        model = QuizAnswerChoice
        fields = ("text", "is_correct")


class AssignmentMetaForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ("title", "instructions", "available_from", "deadline", "attempts_allowed")
        widgets = {
            "deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "available_from": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "instructions": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.deadline:
            d = self.instance.deadline
            if timezone.is_aware(d):
                d = timezone.localtime(d, timezone.get_current_timezone())
            self.initial["deadline"] = d.strftime("%Y-%m-%dT%H:%M")
        if self.instance and getattr(self.instance, "available_from", None):
            a = self.instance.available_from
            if timezone.is_aware(a):
                a = timezone.localtime(a, timezone.get_current_timezone())
            self.initial["available_from"] = a.strftime("%Y-%m-%dT%H:%M")
        # Add client-side min attribute to inputs (current local time)
        try:
            now = timezone.localtime(timezone.now(), timezone.get_current_timezone())
            now_str = now.strftime("%Y-%m-%dT%H:%M")
            if "available_from" in self.fields:
                self.fields["available_from"].widget.attrs.setdefault("min", now_str)
            if "deadline" in self.fields:
                self.fields["deadline"].widget.attrs.setdefault("min", now_str)
        except Exception:
            pass

    def clean_deadline(self):
        d = self.cleaned_data.get("deadline")
        if not d:
            return d
        if timezone.is_naive(d):
            d = timezone.make_aware(d, timezone.get_current_timezone())
        if d <= timezone.now():
            raise forms.ValidationError("Deadline must be in the future.")
        return d

    def clean_available_from(self):
        a = self.cleaned_data.get("available_from")
        if not a:
            return a
        if timezone.is_naive(a):
            a = timezone.make_aware(a, timezone.get_current_timezone())
        return a

    def clean(self):
        cleaned = super().clean()
        a = cleaned.get("available_from")
        d = cleaned.get("deadline")
        if a and d and a >= d:
            self.add_error("available_from", "Availability must be before the deadline.")
        return cleaned

    def clean_attempts_allowed(self):
        val = self.cleaned_data.get("attempts_allowed")
        try:
            val = int(val or 0)
        except Exception:
            raise forms.ValidationError("Invalid attempts value.")
        if val < 1:
            raise forms.ValidationError("Attempts must be at least 1.")
        if getattr(self, 'instance', None) and getattr(self.instance, 'pk', None):
            try:
                from .models import Attempt
                used = Attempt.objects.filter(assignment=self.instance).count()
                if val < used:
                    raise forms.ValidationError(f"Cannot set attempts below attempts already used ({used}).")
            except Exception:
                pass
        return val
