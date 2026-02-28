"""Forms for user registration and profile editing."""
from __future__ import annotations

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile, Role
from django.core.exceptions import ValidationError
from io import BytesIO
from django.core.files.base import ContentFile


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
    """Edit profile details and optional avatar upload (no role change)."""

    avatar = forms.ImageField(required=False)

    class Meta:
        model = UserProfile
        fields = ("full_name", "phone", "avatar")

    def clean_avatar(self):
        f = self.cleaned_data.get("avatar")
        if not f:
            return f
        if getattr(f, "size", 0) > 2 * 1024 * 1024:  # 2 MB limit for avatars
            raise ValidationError("Avatar must be 2 MB or smaller.")
        ctype = getattr(f, "content_type", "")
        if ctype not in ("image/jpeg", "image/png", "image/webp"):
            raise ValidationError("Avatar must be JPEG, PNG, or WEBP.")
        return f

    def save(self, commit: bool = True):
        profile: UserProfile = super().save(commit=False)
        f = self.cleaned_data.get("avatar")
        if f:
            # Resize to max 256px and save as PNG to normalise (if Pillow available)
            try:
                from PIL import Image  # lazy import to avoid hard dependency at import time

                img = Image.open(f)
                img = img.convert("RGBA") if img.mode not in ("RGB", "RGBA") else img
                img.thumbnail((256, 256))
                buf = BytesIO()
                img.save(buf, format="PNG", optimize=True)
                profile.avatar.save(
                    f"avatar_{profile.user_id}.png",
                    ContentFile(buf.getvalue()),
                    save=False,
                )
            except ImportError:
                # If Pillow isn't installed, store the original upload as-is
                profile.avatar = f
            except Exception:
                raise ValidationError("Invalid image file.")
        if commit:
            profile.save()
        return profile
