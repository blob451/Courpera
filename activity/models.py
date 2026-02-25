"""Activity models: simple status updates (Stage 7)."""
from __future__ import annotations

from django.conf import settings
from django.db import models


class Status(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="statuses")
    text = models.CharField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user_id}:{self.text[:20]}"

