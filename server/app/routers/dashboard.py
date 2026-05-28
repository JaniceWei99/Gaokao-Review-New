"""Dashboard router — aggregated home page data."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import get_dashboard

router = APIRouter()


@router.get("", response_model=DashboardResponse)
async def student_dashboard(
    student_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated dashboard data for a student.

    Returns: today's quote, countdowns, active action card,
    upcoming milestones, error notes summary, growth records count,
    and subscription status.
    """
    return await get_dashboard(student_id, user_id, db)
