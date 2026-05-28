"""Action card router — detail, toggle, and set checked items."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.middleware.permission import require_standard
from app.services.action_card_service import (
    get_action_card_detail,
    get_action_card_for_milestone,
    set_checked_items,
    toggle_action_item,
)

router = APIRouter()


class ToggleRequest(BaseModel):
    item_index: int


class SetCheckedRequest(BaseModel):
    checked_indexes: list[int]


@router.get("/cards/{action_card_id}")
async def get_card(
    action_card_id: uuid.UUID,
    student_id: uuid.UUID,
    plan: str = Depends(require_standard),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get an action card with the student's checked state. Requires standard plan."""
    return await get_action_card_detail(action_card_id, student_id, user_id, db)


@router.get("/milestones/{milestone_id}/action-card")
async def get_milestone_action_card(
    milestone_id: uuid.UUID,
    student_id: uuid.UUID,
    plan: str = Depends(require_standard),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the action card for a specific milestone. Requires standard plan."""
    return await get_action_card_for_milestone(milestone_id, student_id, user_id, db)


@router.post("/cards/{action_card_id}/toggle")
async def toggle_item(
    action_card_id: uuid.UUID,
    student_id: uuid.UUID,
    body: ToggleRequest,
    plan: str = Depends(require_standard),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a single action item's checked state. Requires standard plan."""
    return await toggle_action_item(
        action_card_id, body.item_index, student_id, user_id, db
    )


@router.put("/cards/{action_card_id}/checked")
async def set_checked(
    action_card_id: uuid.UUID,
    student_id: uuid.UUID,
    body: SetCheckedRequest,
    plan: str = Depends(require_standard),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Set the full list of checked action item indexes. Requires standard plan."""
    return await set_checked_items(
        action_card_id, body.checked_indexes, student_id, user_id, db
    )
