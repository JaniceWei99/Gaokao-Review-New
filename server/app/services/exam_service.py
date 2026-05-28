"""Exam service — CRUD for exam records and score management."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import (
    DuplicateExamDate,
    FreeLimitExams,
    ResourceNotFound,
    StudentNotFound,
)
from app.models.exam import Exam, ExamScore
from app.models.student import Student
from app.models.subject import Subject
from app.schemas.exam import (
    ExamCreate,
    ExamCreateResponse,
    ExamListResponse,
    ExamResponse,
    ExamScoreResponse,
    ExamTrendResponse,
    LastMaxScoresResponse,
    ProgressDetected,
    TrendPoint,
)
from app.middleware.permission import check_exam_limit


async def list_exams(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> ExamListResponse:
    """List all exams for a student, newest first."""
    await _verify_student(student_id, user_id, db)

    result = await db.execute(
        select(Exam)
        .where(Exam.student_id == student_id)
        .order_by(Exam.exam_date.desc())
    )
    exams = result.scalars().all()

    responses = []
    for e in exams:
        resp = ExamResponse.model_validate(e)
        resp.scores = [ExamScoreResponse.model_validate(s) for s in e.scores]
        responses.append(resp)

    return ExamListResponse(exams=responses)


async def create_exam(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ExamCreate,
    plan: str,
    db: AsyncSession,
) -> ExamCreateResponse:
    """Create a new exam with scores. Checks free-tier limit."""
    await _verify_student(student_id, user_id, db)
    await check_exam_limit(student_id, db, plan)

    existing = await db.execute(
        select(Exam).where(
            Exam.student_id == student_id,
            Exam.name == data.name,
            Exam.exam_date == data.exam_date,
        )
    )
    if existing.scalar_one_or_none():
        raise DuplicateExamDate()

    exam = Exam(
        student_id=student_id,
        name=data.name,
        exam_type=data.exam_type,
        exam_date=data.exam_date,
    )
    db.add(exam)
    await db.flush()

    for score_input in data.scores:
        score_rate = round(score_input.score / score_input.max_score * 100, 2) if score_input.max_score > 0 else 0
        score = ExamScore(
            exam_id=exam.id,
            subject_id=score_input.subject_id,
            score=score_input.score,
            max_score=score_input.max_score,
            score_rate=score_rate,
        )
        db.add(score)

    await db.flush()

    progress = await _detect_progress(student_id, exam, data, db)

    exam_resp = ExamResponse.model_validate(exam)
    exam_resp.scores = [
        ExamScoreResponse.model_validate(s) for s in exam.scores
    ]

    return ExamCreateResponse(
        exam=exam_resp,
        progress_detected=progress if progress else None,
    )


async def delete_exam(
    exam_id: uuid.UUID,
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Delete an exam and its scores."""
    await _verify_student(student_id, user_id, db)

    result = await db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.student_id == student_id)
    )
    exam = result.scalar_one_or_none()
    if exam is None:
        raise ResourceNotFound()

    await db.delete(exam)
    await db.flush()


async def get_last_max_scores(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> LastMaxScoresResponse:
    """Get the most recent max_score for each subject (for UI defaults)."""
    await _verify_student(student_id, user_id, db)

    result = await db.execute(
        select(ExamScore.subject_id, ExamScore.max_score)
        .join(Exam, Exam.id == ExamScore.exam_id)
        .where(Exam.student_id == student_id)
        .order_by(Exam.exam_date.desc())
    )
    rows = result.all()

    last_scores: dict[str, float] = {}
    for subject_id, max_score in rows:
        if subject_id not in last_scores:
            last_scores[subject_id] = float(max_score)

    return LastMaxScoresResponse(last_max_scores=last_scores)


async def _verify_student(
    student_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> Student:
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise StudentNotFound()
    return student


async def _detect_progress(
    student_id: uuid.UUID,
    new_exam: Exam,
    data: ExamCreate,
    db: AsyncSession,
) -> list[ProgressDetected]:
    """Detect if any subject improved by >= 10% compared to the previous same-type exam."""
    prev_result = await db.execute(
        select(Exam)
        .where(
            Exam.student_id == student_id,
            Exam.exam_type == data.exam_type,
            Exam.exam_date < data.exam_date,
        )
        .order_by(Exam.exam_date.desc())
        .limit(1)
    )
    prev_exam = prev_result.scalar_one_or_none()
    if prev_exam is None:
        return []

    prev_scores = {s.subject_id: s for s in prev_exam.scores}
    progress_list = []

    for score_input in data.scores:
        prev_score = prev_scores.get(score_input.subject_id)
        if prev_score and prev_score.score_rate is not None:
            new_rate = round(score_input.score / score_input.max_score * 100, 2) if score_input.max_score > 0 else 0
            improvement = round(new_rate - float(prev_score.score_rate), 2)
            if improvement >= 10.0:
                subject = await db.get(Subject, score_input.subject_id)
                progress_list.append(
                    ProgressDetected(
                        subject_id=score_input.subject_id,
                        subject_name=subject.name if subject else score_input.subject_id,
                        previous_rate=float(prev_score.score_rate),
                        current_rate=new_rate,
                        improvement=improvement,
                    )
                )

    return progress_list


async def get_exam_trend(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    subject_id: str,
    db: AsyncSession,
) -> ExamTrendResponse:
    """Get score trend for a specific subject across all exams."""
    await _verify_student(student_id, user_id, db)

    result = await db.execute(
        select(Exam)
        .where(Exam.student_id == student_id)
        .order_by(Exam.exam_date)
    )
    exams = result.scalars().all()

    trend_points = []
    for exam in exams:
        score = next(
            (s for s in exam.scores if s.subject_id == subject_id), None
        )
        if score:
            trend_points.append(
                TrendPoint(
                    exam_name=exam.name,
                    exam_date=exam.exam_date,
                    score=float(score.score),
                    max_score=float(score.max_score),
                    score_rate=float(score.score_rate) if score.score_rate else 0,
                )
            )

    overall_trend = "stable"
    best_rate = None
    latest_rate = None

    if trend_points:
        rates = [p.score_rate for p in trend_points]
        best_rate = max(rates)
        latest_rate = rates[-1]

        if len(rates) >= 2:
            first_half = rates[: len(rates) // 2]
            second_half = rates[len(rates) // 2 :]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            if avg_second - avg_first >= 5:
                overall_trend = "up"
            elif avg_first - avg_second >= 5:
                overall_trend = "down"

    return ExamTrendResponse(
        trend=trend_points,
        overall_trend=overall_trend,
        best_rate=best_rate,
        latest_rate=latest_rate,
    )
