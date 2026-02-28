from __future__ import annotations

from typing import Dict, Any

from .models import Assignment, QuizQuestion, QuizAnswerChoice


def grade_quiz(assignment: Assignment, selected: dict[int, int]) -> dict[str, Any]:
    """Grade a quiz assignment.

    - assignment: the Assignment instance (type must be 'quiz')
    - selected: mapping of question_id -> choice_id chosen by the student

    Returns: { 'total': int, 'correct': int, 'score': float, 'per_question': {qid: bool} }
    """
    assert assignment.type == "quiz", "grade_quiz only supports quiz assignments"
    questions = list(assignment.questions.all())
    total = len(questions)
    correct = 0
    perq: dict[int, bool] = {}
    # Preload correct choices into a dict
    correct_map: dict[int, int] = {}
    for q in questions:
        correct_choice = q.choices.filter(is_correct=True).first()
        if not correct_choice:
            # If not defined, treat as incorrect by default
            perq[q.id] = False
            continue
        correct_map[q.id] = correct_choice.id

    for q in questions:
        chosen = selected.get(q.id)
        ok = chosen is not None and correct_map.get(q.id) == chosen
        perq[q.id] = ok
        if ok:
            correct += 1

    score = round((correct / total) * 100.0, 2) if total else 0.0
    return {"total": total, "correct": correct, "score": score, "per_question": perq}


def quiz_readiness(assignment: Assignment) -> dict[str, Any]:
    """Evaluate whether a quiz is ready for students to take.

    Conditions:
    - At least one question
    - Each question has exactly one correct answer
    - Each question has at least two choices
    Returns: { 'ready': bool, 'issues': [str] }
    """
    assert assignment.type == "quiz"
    issues: list[str] = []
    qs = list(assignment.questions.all())
    if not qs:
        issues.append("Quiz has no questions.")
    for q in qs:
        correct_count = q.choices.filter(is_correct=True).count()
        if correct_count != 1:
            issues.append(f"Question {q.order or q.id}: must have exactly one correct answer.")
        if q.choices.count() < 2:
            issues.append(f"Question {q.order or q.id}: must have at least two answer choices.")
    return {"ready": len(issues) == 0, "issues": issues}
