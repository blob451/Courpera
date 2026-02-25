"""Course feedback model (Stage 7)."""
from __future__ import annotations

from django.conf import settings
from django.db import models

from .models import Course


class Feedback(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="feedback")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedback")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("course", "student")
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.course_id}:{self.student_id}={self.rating}"

