"""Exams router — CRUD for exam records and scores."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.middleware.permission import get_user_plan
from app.schemas.exam import (
    ExamCreate,
    ExamCreateResponse,
    ExamListResponse,
    ExamTrendResponse,
    LastMaxScoresResponse,
)
from app.services.exam_service import (
    create_exam,
    delete_exam,
    get_exam_trend,
    get_last_max_scores,
    list_exams,
)

router = APIRouter()


@router.get("", response_model=ExamListResponse)
async def list_student_exams(
    student_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all exams for a student."""
    return await list_exams(student_id, user_id, db)


@router.post("", response_model=ExamCreateResponse, status_code=201)
async def create_student_exam(
    student_id: uuid.UUID,
    body: ExamCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    plan: str = Depends(get_user_plan),
    db: AsyncSession = Depends(get_db),
):
    """Record a new exam with scores. Free tier limited to 3 exams."""
    return await create_exam(student_id, user_id, body, plan, db)


@router.delete("/{exam_id}", status_code=204)
async def delete_student_exam(
    student_id: uuid.UUID,
    exam_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete an exam record."""
    await delete_exam(exam_id, student_id, user_id, db)


@router.get("/trend", response_model=ExamTrendResponse)
async def exam_trend(
    student_id: uuid.UUID,
    subject_id: str = Query(..., description="Subject ID to get trend for"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get score trend for a specific subject across all exams."""
    return await get_exam_trend(student_id, user_id, subject_id, db)


@router.get("/last-max-scores", response_model=LastMaxScoresResponse)
async def last_max_scores(
    student_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the most recent max_score for each subject (UI defaults)."""
    return await get_last_max_scores(student_id, user_id, db)
