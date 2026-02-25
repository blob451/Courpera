"""Signals for automatic profile management.

On user creation, create a default `UserProfile` with the student role.
This keeps registration straightforward while still supporting a role
selection UI that updates the profile after creation.
"""
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile, Role


@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created: bool, **kwargs):  # noqa: D401
    """Create a profile for new users (default role: student)."""
    if created:
        UserProfile.objects.create(user=instance, role=Role.STUDENT)

