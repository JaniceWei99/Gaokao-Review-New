"""Error notes API — CRUD and statistics for wrong-answer entries."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.middleware.permission import get_user_plan
from app.schemas.error_note import ErrorNoteCreate, ErrorNoteListResponse, ErrorNoteResponse
from app.services.cache_service import cache_delete
from app.services.error_note_service import (
    create_error_note,
    delete_error_note,
    get_error_note,
    get_error_note_stats,
    list_error_notes,
)

router = APIRouter()


@router.post("", response_model=ErrorNoteResponse, status_code=201)
async def create_note(
    student_id: uuid.UUID,
    body: ErrorNoteCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await create_error_note(student_id, user_id, body, db)
    await cache_delete(f"dashboard:{student_id}")
    return result


@router.get("", response_model=ErrorNoteListResponse)
async def list_notes(
    student_id: uuid.UUID,
    subject_id: str | None = Query(None),
    knowledge_node_id: uuid.UUID | None = Query(None),
    error_type: str | None = Query(None),
    source: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: Literal["newest", "oldest"] = Query("newest"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_error_notes(
        student_id, user_id,
        subject_id=subject_id,
        knowledge_node_id=knowledge_node_id,
        error_type=error_type,
        source=source,
        page=page,
        page_size=page_size,
        sort=sort,
        db=db,
    )


@router.get("/stats")
async def note_stats(
    student_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_error_note_stats(student_id, user_id, db)


@router.get("/{note_id}", response_model=ErrorNoteResponse)
async def get_note(
    student_id: uuid.UUID,
    note_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_error_note(student_id, note_id, user_id, db)


@router.delete("/{note_id}")
async def remove_note(
    student_id: uuid.UUID,
    note_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await delete_error_note(student_id, note_id, user_id, db)
    await cache_delete(f"dashboard:{student_id}")
    return {"success": True}
