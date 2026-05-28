"""Growth records API — CRUD and school-year grouping for student achievements."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.schemas.growth_record import (
    GrowthRecordCreate,
    GrowthRecordCreateResponse,
    GrowthRecordListResponse,
    GrowthRecordResponse,
)
from app.services.growth_record_service import (
    create_growth_record,
    delete_growth_record,
    list_growth_records,
)

router = APIRouter()


@router.post("", response_model=GrowthRecordCreateResponse, status_code=201)
async def create_record(
    student_id: uuid.UUID,
    body: GrowthRecordCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await create_growth_record(student_id, user_id, body, db)


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
    return {"success": True}
