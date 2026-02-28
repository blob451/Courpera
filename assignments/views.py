from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone 
from datetime import timedelta
from django.conf import settings

from accounts.models import Role
from accounts.decorators import role_required
from courses.models import Course, Enrolment

from django.db import models 
from .models import (
    Assignment,
    AssignmentType,
    QuizQuestion,
    QuizAnswerChoice,
    Attempt,
    StudentAnswer,
)
from .forms import AssignmentForm, QuizQuestionForm, QuizAnswerChoiceForm, AssignmentMetaForm 
from .utils import grade_quiz, quiz_readiness


def _is_teacher_owner(user, course: Course) -> bool:
    return bool(user.is_authenticated and getattr(getattr(user, "profile", None), "role", None) == Role.TEACHER and course.owner_id == user.id)


def _is_enrolled(user, course: Course) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return Enrolment.objects.filter(course=course, student=user).exists()


@login_required
def course_assignments(request, course_id: int): 
    course = get_object_or_404(Course, pk=course_id)
    owner = _is_teacher_owner(request.user, course)
    if not (owner or _is_enrolled(request.user, course)):
        raise PermissionDenied
    assignments = Assignment.objects.filter(course=course).prefetch_related("questions__choices").order_by("title") 
    now = timezone.now()
    for a in assignments: 
        if a.type == AssignmentType.QUIZ: 
            setattr(a, "ready_info", quiz_readiness(a)) 
        else: 
            setattr(a, "ready_info", None) 
        setattr(a, "avail_ok", (a.available_from is None) or (now >= a.available_from))
    # For students, compute attempts used/left per assignment
    if not owner:
        ids = [a.id for a in assignments]
        used_qs = (
            Attempt.objects.filter(assignment_id__in=ids, student=request.user)
            .values("assignment_id")
            .annotate(c=models.Count("id"))
        )
        used_map = {row["assignment_id"]: row["c"] for row in used_qs}
        for a in assignments:
            used = used_map.get(a.id, 0)
            setattr(a, "attempts_used", used)
            setattr(a, "attempts_left", max(0, (a.attempts_allowed or 0) - used))
    return render(request, "assignments/course_assignments.html", {"course": course, "assignments": assignments, "owner_view": owner})


@login_required
@role_required(Role.TEACHER)
def assignment_create(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    if not _is_teacher_owner(request.user, course):
        raise PermissionDenied
    if request.method == "POST":
        form = AssignmentForm(request.POST)
        if form.is_valid():
            a = form.save(commit=False)
            a.course = course
            a.save()
            messages.success(request, "Assignment created.") 
            if a.type == AssignmentType.QUIZ: 
                return redirect("assignments:quiz-manage", pk=a.pk) 
            # For Paper/Exam, go directly to generic manage page for meta edits
            return redirect("assignments:manage", pk=a.pk) 
    else:
        form = AssignmentForm()
    return render(request, "assignments/assignment_create.html", {"form": form, "course": course})


@login_required
@role_required(Role.TEACHER)
def assignment_delete(request, pk: int):
    a = get_object_or_404(Assignment.objects.select_related("course"), pk=pk)
    if not _is_teacher_owner(request.user, a.course):
        raise PermissionDenied
    if request.method != "POST":
        messages.error(request, "Please confirm deletion via the form.")
        return redirect("assignments:course", course_id=a.course_id)
    if Attempt.objects.filter(assignment=a).exists():
        messages.error(request, "Cannot delete: attempts exist.")
        return redirect("assignments:course", course_id=a.course_id)
    a.delete()
    messages.success(request, "Assignment deleted.")
    return redirect("assignments:course", course_id=a.course_id)


@login_required
@role_required(Role.TEACHER)
def quiz_manage(request, pk: int): 
    a = get_object_or_404(Assignment.objects.select_related("course"), pk=pk)
    if a.type != AssignmentType.QUIZ:
        messages.error(request, "Not a quiz assignment.")
        return redirect("assignments:course", course_id=a.course_id)
    if not _is_teacher_owner(request.user, a.course):
        raise PermissionDenied
    # Lock structural editing once attempts exist; compute readiness banner
    locked = Attempt.objects.filter(assignment=a).exists()
    ready_info = quiz_readiness(a) if a.type == AssignmentType.QUIZ else {"ready": True, "issues": []}
    q_form = QuizQuestionForm()
    c_form = QuizAnswerChoiceForm()
    meta_form = AssignmentMetaForm(instance=a) 

    if request.method == "POST": 
        action = request.POST.get("action", "") 
        # Meta updates allowed even if locked 
        if action == "update_meta": 
            meta_form = AssignmentMetaForm(request.POST, instance=a) 
            if meta_form.is_valid(): 
                meta_form.save() 
                messages.success(request, "Assignment details updated.") 
                return redirect("assignments:quiz-manage", pk=a.pk) 
        elif action == "set_available_now":
            a.available_from = timezone.now()
            a.save(update_fields=["available_from"]) 
            messages.success(request, "Availability set to now.")
            return redirect("assignments:quiz-manage", pk=a.pk)
        elif action == "set_deadline_delta":
            delta_str = (request.POST.get("deadline_delta") or "").strip()
            mapping = {
                "1d": timedelta(days=1),
                "3d": timedelta(days=3),
                "1w": timedelta(weeks=1),
                "2w": timedelta(weeks=2),
                "1m": timedelta(days=30),
                "3m": timedelta(days=90),
            }
            td = mapping.get(delta_str)
            if td is None:
                messages.error(request, "Invalid deadline option.")
                return redirect("assignments:quiz-manage", pk=a.pk)
            # Prefer posted available_from value if provided in the form
            try:
                tmp_form = AssignmentMetaForm(request.POST, instance=a)
                if tmp_form.is_valid():
                    base = tmp_form.cleaned_data.get("available_from") or a.available_from or timezone.now()
                else:
                    base = a.available_from or timezone.now()
            except Exception:
                base = a.available_from or timezone.now()
            a.deadline = base + td
            a.save(update_fields=["deadline"]) 
            messages.success(request, "Deadline updated.")
            return redirect("assignments:quiz-manage", pk=a.pk)
        elif action == "update_question": 
            qid = int(request.POST.get("question_id", "0")) 
            txt = (request.POST.get("text") or "").strip()
            q = a.questions.filter(pk=qid).first()
            if q and txt:
                q.text = txt
                q.save(update_fields=["text"])
                messages.success(request, "Question updated.")
                return redirect("assignments:quiz-manage", pk=a.pk)
        elif not locked:
            if action == "add_question":
                q_form = QuizQuestionForm(request.POST)
                if q_form.is_valid():
                    q = q_form.save(commit=False)
                    q.assignment = a
                    q.order = (a.questions.aggregate(models.Max("order")) or {}).get("order__max") or 0
                    q.order += 1
                    q.save()
                    messages.success(request, "Question added.")
                    return redirect("assignments:quiz-manage", pk=a.pk)
            elif action == "add_choice": 
                question_id = int(request.POST.get("question_id", "0")) 
                q = a.questions.filter(pk=question_id).first() 
                if q: 
                    c_form = QuizAnswerChoiceForm(request.POST) 
                    if c_form.is_valid(): 
                        c = c_form.save(commit=False) 
                        c.question = q 
                        c.order = (q.choices.aggregate(models.Max("order")) or {}).get("order__max") or 0 
                        c.order += 1 
                        c.save() 
                        if c.is_correct: 
                            q.choices.exclude(pk=c.pk).update(is_correct=False) 
                        messages.success(request, "Answer option added.") 
                        return redirect("assignments:quiz-manage", pk=a.pk) 
            elif action == "delete_question":
                qid = int(request.POST.get("question_id", "0"))
                q = a.questions.filter(pk=qid).first()
                if q:
                    q.delete()
                    messages.success(request, "Question removed.")
                    return redirect("assignments:quiz-manage", pk=a.pk)
            elif action == "delete_choice": 
                cid = int(request.POST.get("choice_id", "0")) 
                ch = QuizAnswerChoice.objects.filter(pk=cid, question__assignment=a).first() 
                if ch: 
                    # Prevent removing below 2 options on published quizzes
                    q = ch.question
                    if a.is_published and q.choices.count() <= 2:
                        messages.error(request, "Cannot delete: a published question must have at least two choices.")
                        return redirect("assignments:quiz-manage", pk=a.pk)
                    ch.delete() 
                    messages.success(request, "Answer option removed.") 
                    return redirect("assignments:quiz-manage", pk=a.pk) 
            elif action == "mark_correct":
                cid = int(request.POST.get("choice_id", "0"))
                ch = QuizAnswerChoice.objects.filter(pk=cid, question__assignment=a).select_related("question").first()
                if ch:
                    QuizAnswerChoice.objects.filter(question=ch.question).update(is_correct=False)
                    ch.is_correct = True
                    ch.save(update_fields=["is_correct"])
                    messages.success(request, "Marked as correct.")
                    return redirect("assignments:quiz-manage", pk=a.pk)
            elif action == "publish": 
                if not ready_info["ready"]: 
                    messages.error(request, "Quiz is not ready; fix issues before publishing.") 
                else: 
                    # Default dates: set availability to now and deadline to one week after if not set
                    if not a.available_from:
                        a.available_from = timezone.now()
                    if not a.deadline:
                        base = a.available_from or timezone.now()
                        a.deadline = base + timedelta(days=7)
                    a.is_published = True 
                    a.save(update_fields=["available_from", "deadline", "is_published"]) 
                    messages.success(request, "Quiz published.") 
                return redirect("assignments:quiz-manage", pk=a.pk) 
            elif action == "unpublish":
                if Attempt.objects.filter(assignment=a).exists():
                    messages.error(request, "Cannot unpublish: attempts exist.")
                else:
                    a.is_published = False
                    a.save(update_fields=["is_published"])
                    messages.success(request, "Quiz unpublished.")
                return redirect("assignments:quiz-manage", pk=a.pk)
    return render(request, "assignments/quiz_manage.html", {"assignment": a, "locked": locked, "q_form": q_form, "c_form": c_form, "ready_info": ready_info, "meta_form": meta_form}) 


@login_required
def assignment_take(request, pk: int): 
    a = get_object_or_404(Assignment.objects.select_related("course"), pk=pk)
    # Permission: enrolled or owner
    if not (_is_enrolled(request.user, a.course) or _is_teacher_owner(request.user, a.course)):
        raise PermissionDenied
    # Availability/deadline/attempts check (only enforced for students) 
    owner = _is_teacher_owner(request.user, a.course) 
    if not owner:
        if not a.is_published:
            messages.error(request, "Assignment is not published.")
            return redirect("assignments:course", course_id=a.course_id)
        if a.is_published and a.available_from and timezone.now() < a.available_from:
            messages.error(request, "Assignment is not available yet.")
            return redirect("assignments:course", course_id=a.course_id)
        if a.deadline and timezone.now() >= a.deadline: 
            messages.error(request, "Deadline has passed.") 
            return redirect("assignments:course", course_id=a.course_id) 
        used = Attempt.objects.filter(assignment=a, student=request.user).count() 
        if used >= a.attempts_allowed: 
            messages.error(request, "No attempts left.") 
            return redirect("assignments:course", course_id=a.course_id) 
    if a.type == AssignmentType.QUIZ: 
        if not a.is_published: 
            messages.error(request, "Assignment is not published.") 
            return redirect("assignments:course", course_id=a.course_id) 
        qs = a.questions.prefetch_related("choices") 
        # Validate quiz readiness: at least 1 question, each has exactly 1 correct
        if qs.count() == 0:
            messages.error(request, "Quiz has no questions yet.")
            return redirect("assignments:course", course_id=a.course_id)
        for q in qs:
            if q.choices.filter(is_correct=True).count() != 1:
                messages.error(request, "Quiz is not ready (each question must have exactly one correct answer).")
                return redirect("assignments:course", course_id=a.course_id)
            if q.choices.count() < 2:
                messages.error(request, "Quiz is not ready (each question must have at least two answer choices).")
                return redirect("assignments:course", course_id=a.course_id)
        used = Attempt.objects.filter(assignment=a, student=request.user).count()
        left = max(0, a.attempts_allowed - used)
        return render(request, "assignments/take_quiz.html", {"assignment": a, "questions": qs, "attempts_used": used, "attempts_left": left}) 
    if a.type == AssignmentType.PAPER: 
        used = Attempt.objects.filter(assignment=a, student=request.user).count()
        left = max(0, a.attempts_allowed - used)
        return render(request, "assignments/take_paper.html", {"assignment": a, "attempts_used": used, "attempts_left": left}) 
    if a.type == AssignmentType.EXAM: 
        used = Attempt.objects.filter(assignment=a, student=request.user).count()
        left = max(0, a.attempts_allowed - used)
        return render(request, "assignments/take_exam.html", {"assignment": a, "questions": a.questions.all(), "attempts_used": used, "attempts_left": left}) 
    used = Attempt.objects.filter(assignment=a, student=request.user).count()
    left = max(0, a.attempts_allowed - used)
    return render(request, "assignments/take_generic.html", {"assignment": a, "attempts_used": used, "attempts_left": left}) 


@login_required
def assignment_submit(request, pk: int): 
    if request.method != "POST":
        return redirect("assignments:take", pk=pk)
    a = get_object_or_404(Assignment.objects.select_related("course"), pk=pk)
    if not _is_enrolled(request.user, a.course): 
        raise PermissionDenied 
    # Enforce availability, deadline and attempts 
    if not a.is_published:
        messages.error(request, "Assignment is not published.")
        return redirect("assignments:course", course_id=a.course_id)
    if a.available_from and timezone.now() < a.available_from:
        messages.error(request, "Assignment is not available yet.")
        return redirect("assignments:course", course_id=a.course_id)
    if a.deadline and timezone.now() >= a.deadline: 
        messages.error(request, "Deadline has passed.") 
        return redirect("assignments:course", course_id=a.course_id) 
    used = Attempt.objects.filter(assignment=a, student=request.user).count()
    if used >= a.attempts_allowed:
        messages.error(request, "No attempts left.")
        return redirect("assignments:course", course_id=a.course_id)

    attempt = Attempt.objects.create(assignment=a, student=request.user, attempt_no=used + 1, submitted_at=timezone.now())
    if a.type == AssignmentType.QUIZ:
        # Expect POST vars: answer_<question.id> = choice.id
        selected: dict[int, int] = {}
        for q in a.questions.all():
            key = f"answer_{q.id}"
            val = request.POST.get(key)
            if not val:
                messages.error(request, "Please answer all questions.")
                attempt.delete()
                return redirect("assignments:take", pk=a.pk)
            try:
                cid = int(val)
            except Exception:
                messages.error(request, "Invalid answer selection.")
                attempt.delete()
                return redirect("assignments:take", pk=a.pk)
            # Validate that choice belongs to question
            if not QuizAnswerChoice.objects.filter(pk=cid, question=q).exists():
                messages.error(request, "Invalid answer selection.")
                attempt.delete()
                return redirect("assignments:take", pk=a.pk)
            StudentAnswer.objects.create(attempt=attempt, question=q, choice_id=cid)
            selected[q.id] = cid
        res = grade_quiz(a, selected)
        attempt.score = res["score"]
        attempt.save(update_fields=["score"]) 
        return redirect("assignments:feedback", attempt_id=attempt.id)
    if a.type == AssignmentType.PAPER:
        # Expect file under 'submission_file'
        f = request.FILES.get("submission_file")
        if not f:
            messages.error(request, "Please upload a file.")
            attempt.delete()
            return redirect("assignments:take", pk=a.pk)
        # Basic validation: size and mime
        maxb = getattr(settings, "FILE_UPLOAD_MAX_MEMORY_SIZE", 25 * 1024 * 1024)
        if getattr(f, "size", 0) > maxb:
            messages.error(request, "File too large.")
            attempt.delete()
            return redirect("assignments:take", pk=a.pk)
        ctype = getattr(f, "content_type", "")
        allowed = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        if ctype not in allowed:
            messages.error(request, "Unsupported file type. Please upload PDF or Word document.")
            attempt.delete()
            return redirect("assignments:take", pk=a.pk)
        from .models import StudentFileSubmission
        StudentFileSubmission.objects.create(attempt=attempt, file=f)
        return redirect("assignments:feedback", attempt_id=attempt.id)
    if a.type == AssignmentType.EXAM:
        # Require at least some text for each question
        for q in a.questions.all():
            key = f"text_{q.id}"
            txt = (request.POST.get(key) or "").strip()
            if not txt:
                messages.error(request, "Please answer all questions.")
                attempt.delete()
                return redirect("assignments:take", pk=a.pk)
            from .models import StudentTextAnswer
            StudentTextAnswer.objects.create(attempt=attempt, question=q, text=txt)
        return redirect("assignments:feedback", attempt_id=attempt.id)
    return redirect("assignments:feedback", attempt_id=attempt.id)


@login_required
def attempt_feedback(request, attempt_id: int):
    att = get_object_or_404(Attempt.objects.select_related("assignment", "student", "assignment__course"), pk=attempt_id)
    a = att.assignment
    # Permissions: student who submitted, or course owner
    if not (att.student_id == request.user.id or _is_teacher_owner(request.user, a.course)):
        raise PermissionDenied
    ctx = {"attempt": att, "assignment": a}
    if a.type == AssignmentType.QUIZ:
        # Build mapping for per-question correctness
        answers = {sa.question_id: sa.choice_id for sa in att.answers.select_related("question", "choice")}
        res = grade_quiz(a, answers)
        ctx.update({"questions": a.questions.prefetch_related("choices"), "answers": answers, "perq": res["per_question"], "score": res["score"]})
        return render(request, "assignments/feedback_quiz.html", ctx)
    return render(request, "assignments/feedback_generic.html", ctx)


@login_required
@role_required(Role.TEACHER)
def assignment_manage(request, pk: int):
    """Generic manage view for Paper/Exam assignments.

    - Paper: manage meta (title, availability, deadline, attempts), publish/unpublish.
    - Exam: same as Paper, plus text-only question add/edit/delete. Locked when attempts exist.
    """
    a = get_object_or_404(Assignment.objects.select_related("course"), pk=pk)
    if a.type == AssignmentType.QUIZ:
        return redirect("assignments:quiz-manage", pk=pk)
    if not _is_teacher_owner(request.user, a.course):
        raise PermissionDenied

    locked = Attempt.objects.filter(assignment=a).exists()
    meta_form = AssignmentMetaForm(instance=a)
    q_form = QuizQuestionForm()

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "update_meta":
            meta_form = AssignmentMetaForm(request.POST, instance=a)
            if meta_form.is_valid():
                meta_form.save()
                messages.success(request, "Assignment details updated.")
                return redirect("assignments:manage", pk=a.pk)
        elif action == "set_available_now":
            a.available_from = timezone.now()
            a.save(update_fields=["available_from"])
            messages.success(request, "Availability set to now.")
            return redirect("assignments:manage", pk=a.pk)
        elif action == "set_deadline_delta":
            delta_str = (request.POST.get("deadline_delta") or "").strip()
            mapping = {
                "1d": timedelta(days=1),
                "3d": timedelta(days=3),
                "1w": timedelta(weeks=1),
                "2w": timedelta(weeks=2),
                "1m": timedelta(days=30),
                "3m": timedelta(days=90),
            }
            td = mapping.get(delta_str)
            if td is None:
                messages.error(request, "Invalid deadline option.")
                return redirect("assignments:manage", pk=a.pk)
            try:
                tmp_form = AssignmentMetaForm(request.POST, instance=a)
                if tmp_form.is_valid():
                    base = tmp_form.cleaned_data.get("available_from") or a.available_from or timezone.now()
                else:
                    base = a.available_from or timezone.now()
            except Exception:
                base = a.available_from or timezone.now()
            a.deadline = base + td
            a.save(update_fields=["deadline"]) 
            messages.success(request, "Deadline updated.")
            return redirect("assignments:manage", pk=a.pk)
        elif not locked and a.type == AssignmentType.EXAM:
            if action == "add_question":
                q_form = QuizQuestionForm(request.POST)
                if q_form.is_valid():
                    q = q_form.save(commit=False)
                    q.assignment = a
                    q.order = (a.questions.aggregate(models.Max("order")) or {}).get("order__max") or 0
                    q.order += 1
                    q.save()
                    messages.success(request, "Question added.")
                    return redirect("assignments:manage", pk=a.pk)
            elif action == "update_question":
                qid = int(request.POST.get("question_id", "0"))
                txt = (request.POST.get("text") or "").strip()
                q = a.questions.filter(pk=qid).first()
                if q and txt:
                    q.text = txt
                    q.save(update_fields=["text"])
                    messages.success(request, "Question updated.")
                    return redirect("assignments:manage", pk=a.pk)
            elif action == "delete_question":
                qid = int(request.POST.get("question_id", "0"))
                q = a.questions.filter(pk=qid).first()
                if q:
                    q.delete()
                    messages.success(request, "Question removed.")
                    return redirect("assignments:manage", pk=a.pk)
        elif action == "publish":
            # Default dates: set availability to now and deadline to one week after if not set
            if not a.available_from:
                a.available_from = timezone.now()
            if not a.deadline:
                base = a.available_from or timezone.now()
                a.deadline = base + timedelta(days=7)
            a.is_published = True
            a.save(update_fields=["available_from", "deadline", "is_published"])
            messages.success(request, "Assignment published.")
            return redirect("assignments:manage", pk=a.pk)
        elif action == "unpublish":
            if Attempt.objects.filter(assignment=a).exists():
                messages.error(request, "Cannot unpublish: attempts exist.")
            else:
                a.is_published = False
                a.save(update_fields=["is_published"])
                messages.success(request, "Assignment unpublished.")
            return redirect("assignments:manage", pk=a.pk)

    return render(
        request,
        "assignments/manage_generic.html",
        {"assignment": a, "locked": locked, "meta_form": meta_form, "q_form": q_form},
    )
