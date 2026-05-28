"""AI features router — premium AI features endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.middleware.permission import require_premium
from app.services.ai_action_suggestion_service import generate_action_suggestions
from app.services.ai_error_classify_service import batch_classify_error_notes, classify_error_note
from app.services.ai_monthly_report_service import generate_monthly_report
from app.services.ai_quote_service import generate_personalized_quote

router = APIRouter()


@router.get("/action-suggestions")
async def get_action_suggestions(
    student_id: uuid.UUID,
    plan: str = Depends(require_premium),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-generated personalized action suggestions. Requires premium plan."""
    return await generate_action_suggestions(student_id, user_id, db)


@router.get("/personalized-quote")
async def get_personalized_quote(
    student_id: uuid.UUID,
    plan: str = Depends(require_premium),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get an AI-generated personalized quote. Requires premium plan."""
    return await generate_personalized_quote(student_id, user_id, db)


@router.post("/error-notes/{error_note_id}/classify")
async def classify_error(
    student_id: uuid.UUID,
    error_note_id: uuid.UUID,
    plan: str = Depends(require_premium),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Classify an error note to knowledge points using AI. Requires premium plan."""
    return await classify_error_note(error_note_id, student_id, user_id, db)


@router.get("/error-notes/classification-summary")
async def error_classification_summary(
    student_id: uuid.UUID,
    subject_id: str | None = Query(None),
    plan: str = Depends(require_premium),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-powered error note classification summary. Requires premium plan."""
    return await batch_classify_error_notes(student_id, user_id, subject_id, db)


@router.get("/monthly-report")
async def get_monthly_report(
    student_id: uuid.UUID,
    year: int = Query(..., ge=2024, le=2030),
    month: int = Query(..., ge=1, le=12),
    plan: str = Depends(require_premium),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-generated monthly growth report. Requires premium plan."""
    return await generate_monthly_report(student_id, user_id, year, month, db)
