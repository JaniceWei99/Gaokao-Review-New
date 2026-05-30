"""Subjects router — list subjects with province-aware max scores."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.subject import Subject
from app.services.subject_config import get_default_max_score
from fastapi import Depends

router = APIRouter()


@router.get("")
async def list_subjects(
    province: str = Query("shanghai", description="Province ID for score resolution"),
    db: AsyncSession = Depends(get_db),
):
    """List all subjects with max scores resolved for the given province.

    The gaokao_max_score returned is province-aware:
    - If the province config has an override, that value is used
    - Otherwise the subject's default is returned
    """
    result = await db.execute(
        select(Subject).order_by(Subject.display_order)
    )
    subjects = result.scalars().all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "gaokao_max_score": get_default_max_score(s.id, province),
            "display_order": s.display_order,
            "icon": s.icon,
        }
        for s in subjects
    ]
