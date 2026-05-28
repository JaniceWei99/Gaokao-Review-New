"""Dashboard router — aggregated home page data with caching."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.schemas.dashboard import DashboardResponse
from app.services.cache_service import cache_get, cache_set
from app.services.dashboard_service import get_dashboard

router = APIRouter()

DASHBOARD_CACHE_TTL = 120


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
    cache_key = f"dashboard:{student_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    result = await get_dashboard(student_id, user_id, db)

    await cache_set(cache_key, result.model_dump(), ttl=DASHBOARD_CACHE_TTL)

    return result
