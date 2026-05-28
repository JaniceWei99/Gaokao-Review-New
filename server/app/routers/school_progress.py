"""School progress API — CRUD and error-note linkage."""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.middleware.permission import require_standard
from app.services.school_progress_service import (
    create_school_progress,
    delete_school_progress,
    get_linked_errors,
    list_school_progress,
    update_school_progress,
)

router = APIRouter()


class ProgressCreate(BaseModel):
    subject_id: str = Field(..., max_length=20)
    content: str = Field(..., max_length=200)
    start_date: str | None = None
    end_date: str | None = None
    knowledge_node_id: str | None = None


class ProgressUpdate(BaseModel):
    content: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    knowledge_node_id: str | None = None


@router.get("")
async def list_progress(
    student_id: uuid.UUID,
    subject_id: str | None = Query(None),
    plan: str = Depends(require_standard),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_school_progress(student_id, user_id, subject_id, db)


@router.post("", status_code=201)
async def create_progress(
    student_id: uuid.UUID,
    body: ProgressCreate,
    plan: str = Depends(require_standard),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await create_school_progress(
        student_id, user_id,
        subject_id=body.subject_id,
        content=body.content,
        start_date=body.start_date,
        end_date=body.end_date,
        knowledge_node_id=body.knowledge_node_id,
        db=db,
    )


@router.put("/{progress_id}")
async def update_progress(
    student_id: uuid.UUID,
    progress_id: uuid.UUID,
    body: ProgressUpdate,
    plan: str = Depends(require_standard),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await update_school_progress(
        student_id, progress_id, user_id,
        content=body.content,
        start_date=body.start_date,
        end_date=body.end_date,
        knowledge_node_id=body.knowledge_node_id,
        db=db,
    )


@router.delete("/{progress_id}")
async def remove_progress(
    student_id: uuid.UUID,
    progress_id: uuid.UUID,
    plan: str = Depends(require_standard),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await delete_school_progress(student_id, progress_id, user_id, db)
    return {"success": True}


@router.get("/{progress_id}/errors")
async def linked_errors(
    student_id: uuid.UUID,
    progress_id: uuid.UUID,
    plan: str = Depends(require_standard),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_linked_errors(student_id, progress_id, user_id, db)
