"""
Student assessment helpers for SkillNova.

The assessment system uses MCQs and produces categorical skill statuses.
Numeric scores are kept internally only and are not shown to students.
"""

from typing import Any


# Student-facing skill status labels.
STRONG = "Strong"
DEVELOPING = "Developing"
NEEDS_IMPROVEMENT = "Needs Improvement"
NOT_ASSESSED = "Not Assessed"


def calculate_skill_status(score: int, total_questions: int) -> str:
    """
    Convert an internal MCQ score into a student-facing skill status.

    Rules:
        80% or above  -> Strong
        50% to 79%   -> Developing
        below 50%    -> Needs Improvement
        no questions -> Not Assessed
    """

    if total_questions <= 0:
        return NOT_ASSESSED

    percentage = (score / total_questions) * 100

    if percentage >= 80:
        return STRONG

    if percentage >= 50:
        return DEVELOPING

    return NEEDS_IMPROVEMENT


def calculate_percentage(score: int, total_questions: int) -> int:
    """Return the internal percentage for an assessment result."""

    if total_questions <= 0:
        return 0

    return round((score / total_questions) * 100)


def validate_option(option: str) -> bool:
    """Check whether an MCQ answer option is valid."""

    return option.upper() in {"A", "B", "C", "D"}


def normalize_option(option: str) -> str:
    """Normalize a submitted MCQ option."""

    return option.strip().upper()


def grade_answer(
    selected_option: str,
    correct_option: str,
) -> bool:
    """Return True when the student's selected option is correct."""

    selected = normalize_option(selected_option)
    correct = normalize_option(correct_option)

    return selected == correct


def build_question_result(
    question: dict[str, Any],
    selected_option: str,
) -> dict[str, Any]:
    """
    Build the result shown after assessment submission.

    The correct answer is intentionally returned only after submission.
    """

    selected = normalize_option(selected_option)
    correct = normalize_option(str(question["correct_option"]))

    return {
        "question_id": question["id"],
        "question": question["question"],
        "selected_option": selected,
        "correct_option": correct,
        "is_correct": selected == correct,
        "explanation": question.get("explanation", ""),
    }


def build_skill_result(
    skill_id: int,
    skill_name: str,
    correct_count: int,
    total_questions: int,
) -> dict[str, Any]:
    """Build the result for one skill."""

    percentage = calculate_percentage(
        correct_count,
        total_questions,
    )

    return {
        "skill_id": skill_id,
        "skill": skill_name,
        "percentage": percentage,
        "status": calculate_skill_status(
            correct_count,
            total_questions,
        ),
        "correct": correct_count,
        "total": total_questions,
    }