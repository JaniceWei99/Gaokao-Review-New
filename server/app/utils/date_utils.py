"""Date and countdown utility functions."""

from __future__ import annotations

from datetime import date, datetime, timezone


def days_until(target: date | str) -> int:
    """Calculate days from today to a target date (positive = future)."""
    if isinstance(target, str):
        target = date.fromisoformat(target)
    today = date.today()
    return (target - today).days


def calculate_phase(grade: str, days_to_nearest_exam: int | None = None) -> str:
    """Determine the current exam-preparation phase for a student.

    Returns one of: 'normal', 'pre_exam_30d', 'pre_exam_7d', 'post_exam', 'all'
    """
    if days_to_nearest_exam is None:
        return "normal"

    if days_to_nearest_exam <= 0:
        return "post_exam"
    if days_to_nearest_exam <= 7:
        return "pre_exam_7d"
    if days_to_nearest_exam <= 30:
        return "pre_exam_30d"
    return "normal"


def school_year_for(date_val: date | None = None) -> str:
    """Return the school year string for a given date, e.g. '2025-2026'.

    A school year starts in September: dates from Sep-Dec belong to the
    year that started, dates from Jan-Aug belong to the previous start year.
    """
    if date_val is None:
        date_val = date.today()
    if date_val.month >= 9:
        return f"{date_val.year}-{date_val.year + 1}"
    return f"{date_val.year - 1}-{date_val.year}"


def now_utc() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)
