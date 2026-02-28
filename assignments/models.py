from __future__ import annotations

from django.db import models
from django.conf import settings
from django.utils import timezone

from courses.models import Course


class AssignmentType(models.TextChoices):
    QUIZ = "quiz", "Quiz"
    PAPER = "paper", "Paper"
    EXAM = "exam", "Exam"


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    type = models.CharField(max_length=16, choices=AssignmentType.choices)
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    # New: availability date/time when students can access the assignment
    available_from = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    attempts_allowed = models.PositiveSmallIntegerField(default=1)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_type_display()})"

    def is_open(self) -> bool:
        if not self.deadline:
            return True
        return timezone.now() < self.deadline

    def is_available(self) -> bool:
        """Whether the assignment is available to students based on availability time.

        Returns True if `available_from` is not set or the current time is
        after the availability start.
        """
        if not self.available_from:
            return True
        return timezone.now() >= self.available_from


class QuizQuestion(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="questions")
    order = models.PositiveSmallIntegerField(default=0)
    text = models.TextField()

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"Q{self.order}: {self.text[:40]}"


class QuizAnswerChoice(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="choices")
    order = models.PositiveSmallIntegerField(default=0)
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"Choice {self.order} ({'✓' if self.is_correct else ' '})"


class Attempt(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignment_attempts")
    attempt_no = models.PositiveSmallIntegerField(default=1)
    submitted_at = models.DateTimeField(default=timezone.now)
    score = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"Attempt {self.attempt_no} by {self.student_id} on {self.assignment_id}"


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    choice = models.ForeignKey(QuizAnswerChoice, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("attempt", "question")


class StudentTextAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="text_answers")
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    text = models.TextField()


class StudentFileSubmission(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="file_submissions")
    file = models.FileField(upload_to="assignment_submissions/")
