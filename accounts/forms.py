"""Forms for user registration and profile editing."""
from __future__ import annotations

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile, Role


class RegistrationForm(UserCreationForm):
    """User registration form with a role selector.

    The role field writes to the related `UserProfile` after the `User`
    instance is created. This avoids having to override the auth user
    model in early stages.
    """

    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Role.choices, initial=Role.STUDENT)

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")

    def save(self, commit: bool = True) -> User:
        user = super().save(commit)
        # Update or create profile role selection
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = self.cleaned_data.get("role") or Role.STUDENT
        profile.save(update_fields=["role"])  # explicit for clarity
        return user

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("E-mail is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this e-mail already exists.")
        return email

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class ProfileForm(forms.ModelForm):
    """Simple form to edit profile contact fields and role."""

    class Meta:
        model = UserProfile
        fields = ("full_name", "phone", "student_number", "role")
