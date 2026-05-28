"""Growth records API — CRUD, school-year grouping, and export for student achievements."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.middleware.permission import require_standard
from app.schemas.growth_record import (
    GrowthRecordCreate,
    GrowthRecordCreateResponse,
    GrowthRecordListResponse,
    GrowthRecordResponse,
)
from app.services.cache_service import cache_delete
from app.services.growth_record_service import (
    create_growth_record,
    delete_growth_record,
    list_growth_records,
)
from app.services.growth_export_service import export_growth_profile

router = APIRouter()


class ExportResponse(BaseModel):
    image_url: str


@router.post("", response_model=GrowthRecordCreateResponse, status_code=201)
async def create_record(
    student_id: uuid.UUID,
    body: GrowthRecordCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await create_growth_record(student_id, user_id, body, db)
    await cache_delete(f"dashboard:{student_id}")
    return result


@router.get("", response_model=GrowthRecordListResponse)
async def list_records(
    student_id: uuid.UUID,
    record_type: str | None = Query(None),
    year: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_growth_records(
        student_id, user_id,
        record_type=record_type,
        year=year,
        page=page,
        page_size=page_size,
        db=db,
    )


@router.delete("/{record_id}")
async def remove_record(
    student_id: uuid.UUID,
    record_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await delete_growth_record(student_id, record_id, user_id, db)
    await cache_delete(f"dashboard:{student_id}")
    return {"success": True}


@router.get("/export", response_model=ExportResponse)
async def export_records(
    student_id: uuid.UUID,
    year: int | None = Query(None),
    plan: str = Depends(require_standard),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export growth records as a long image. Requires standard plan."""
    image_url = await export_growth_profile(student_id, user_id, year, db)
    return ExportResponse(image_url=image_url)
