"""Milestones router — timeline, CRUD for custom milestones."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.schemas.milestone import (
    MilestoneCreate,
    MilestoneListResponse,
    MilestoneResponse,
    MilestoneUpdate,
    NextMilestoneResponse,
)
from app.services.milestone_service import (
    create_custom_milestone,
    delete_custom_milestone,
    get_next_milestone,
    list_milestones,
    update_custom_milestone,
)

router = APIRouter()


@router.get("", response_model=MilestoneListResponse)
async def list_student_milestones(
    student_id: uuid.UUID,
    current: bool = Query(False, description="Only show future milestones"),
    limit: int | None = Query(None, description="Max number of results"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List milestones applicable to a student."""
    return await list_milestones(student_id, user_id, db, current_only=current, limit=limit)


@router.get("/next", response_model=NextMilestoneResponse)
async def next_milestone(
    student_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the next upcoming milestone with action card."""
    return await get_next_milestone(student_id, user_id, db)


@router.post("", response_model=MilestoneResponse, status_code=201)
async def create_milestone(
    student_id: uuid.UUID,
    body: MilestoneCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom milestone for a student."""
    return await create_custom_milestone(student_id, user_id, body, db)


@router.put("/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    student_id: uuid.UUID,
    milestone_id: uuid.UUID,
    body: MilestoneUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a custom milestone."""
    return await update_custom_milestone(milestone_id, student_id, user_id, body, db)


@router.delete("/{milestone_id}", status_code=204)
async def delete_milestone(
    student_id: uuid.UUID,
    milestone_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom milestone (system milestones cannot be deleted)."""
    await delete_custom_milestone(milestone_id, student_id, user_id, db)
