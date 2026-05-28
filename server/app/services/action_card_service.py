"""Action card service — retrieve action cards with checked state persistence."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import FeatureRequiresStandard, ResourceNotFound, StudentNotFound
from app.models.action_card import ActionCard
from app.models.milestone import Milestone, MilestoneReminder
from app.models.student import Student
from app.schemas.milestone import ActionCardResponse

logger = logging.getLogger(__name__)


async def get_action_card_detail(
    action_card_id: uuid.UUID,
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Get an action card with the student's checked items."""
    await _verify_student(student_id, user_id, db)

    result = await db.execute(
        select(ActionCard).where(ActionCard.id == action_card_id)
    )
    card = result.scalar_one_or_none()
    if card is None:
        raise ResourceNotFound()

    checked_indexes = await _get_checked_indexes(action_card_id, student_id, db)

    return _build_card_response(card, checked_indexes)


async def get_action_card_for_milestone(
    milestone_id: uuid.UUID,
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Get the action card for a specific milestone, based on days remaining."""
    await _verify_student(student_id, user_id, db)

    from app.utils.date_utils import days_until

    result = await db.execute(
        select(Milestone).where(Milestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        raise ResourceNotFound()

    days = days_until(milestone.event_date)

    action_card_id = None
    timing = None
    if days <= 3 and milestone.action_card_3d_id:
        action_card_id = milestone.action_card_3d_id
        timing = "3d_before"
    elif days <= 15 and milestone.action_card_15d_id:
        action_card_id = milestone.action_card_15d_id
        timing = "15d_before"

    if action_card_id is None:
        return {
            "action_card": None,
            "timing": None,
            "checked_indexes": [],
            "progress": 0,
        }

    card_result = await db.execute(
        select(ActionCard).where(ActionCard.id == action_card_id)
    )
    card = card_result.scalar_one_or_none()
    if card is None:
        return {
            "action_card": None,
            "timing": None,
            "checked_indexes": [],
            "progress": 0,
        }

    checked_indexes = await _get_checked_indexes(action_card_id, student_id, db)

    total = len(card.action_items) if card.action_items else 0
    done = len(checked_indexes)
    progress = round(done / total, 2) if total > 0 else 0

    return {
        "action_card": ActionCardResponse.model_validate(card),
        "timing": timing,
        "checked_indexes": checked_indexes,
        "progress": progress,
    }


async def toggle_action_item(
    action_card_id: uuid.UUID,
    item_index: int,
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Toggle the checked state of a single action item."""
    await _verify_student(student_id, user_id, db)

    result = await db.execute(
        select(ActionCard).where(ActionCard.id == action_card_id)
    )
    card = result.scalar_one_or_none()
    if card is None:
        raise ResourceNotFound()

    total_items = len(card.action_items) if card.action_items else 0
    if item_index < 0 or item_index >= total_items:
        from app.middleware.error_handler import InvalidParams
        raise InvalidParams(f"item_index {item_index} out of range (0-{total_items - 1})")

    checked = await _get_checked_indexes(action_card_id, student_id, db)

    if item_index in checked:
        checked.remove(item_index)
    else:
        checked.append(item_index)

    await _save_checked_indexes(action_card_id, student_id, db, checked)

    done = len(checked)
    progress = round(done / total_items, 2) if total_items > 0 else 0

    return {
        "checked_indexes": sorted(checked),
        "progress": progress,
    }


async def set_checked_items(
    action_card_id: uuid.UUID,
    checked_indexes: list[int],
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Set the full list of checked action item indexes."""
    await _verify_student(student_id, user_id, db)

    result = await db.execute(
        select(ActionCard).where(ActionCard.id == action_card_id)
    )
    card = result.scalar_one_or_none()
    if card is None:
        raise ResourceNotFound()

    total_items = len(card.action_items) if card.action_items else 0
    for idx in checked_indexes:
        if idx < 0 or idx >= total_items:
            from app.middleware.error_handler import InvalidParams
            raise InvalidParams(f"item_index {idx} out of range (0-{total_items - 1})")

    await _save_checked_indexes(action_card_id, student_id, db, checked_indexes)

    done = len(checked_indexes)
    progress = round(done / total_items, 2) if total_items > 0 else 0

    return {
        "checked_indexes": sorted(checked_indexes),
        "progress": progress,
    }


async def _verify_student(
    student_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> Student:
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise StudentNotFound()
    return student


async def _get_checked_indexes(
    action_card_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession,
) -> list[int]:
    result = await db.execute(
        select(MilestoneReminder).where(
            MilestoneReminder.student_id == student_id,
        )
    )
    reminders = result.scalars().all()

    for reminder in reminders:
        milestone = await db.get(Milestone, reminder.milestone_id)
        if milestone is None:
            continue
        if milestone.action_card_15d_id == action_card_id or milestone.action_card_3d_id == action_card_id:
            raw = reminder.action_items_checked or []
            return list(set(raw))

    return []


async def _save_checked_indexes(
    action_card_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession,
    checked_indexes: list[int],
) -> None:
    target_reminder = None
    target_milestone = None

    result = await db.execute(
        select(MilestoneReminder).where(
            MilestoneReminder.student_id == student_id,
        )
    )
    reminders = result.scalars().all()

    for reminder in reminders:
        milestone = await db.get(Milestone, reminder.milestone_id)
        if milestone is None:
            continue
        if milestone.action_card_15d_id == action_card_id or milestone.action_card_3d_id == action_card_id:
            target_reminder = reminder
            target_milestone = milestone
            break

    if target_reminder:
        target_reminder.action_items_checked = sorted(checked_indexes)
    else:
        result = await db.execute(
            select(ActionCard).where(ActionCard.id == action_card_id)
        )
        card = result.scalar_one_or_none()
        if card is None:
            raise ResourceNotFound()

        milestone_result = await db.execute(
            select(Milestone).where(
                (Milestone.action_card_15d_id == action_card_id)
                | (Milestone.action_card_3d_id == action_card_id)
            ).limit(1)
        )
        milestone = milestone_result.scalar_one_or_none()
        if milestone is None:
            raise ResourceNotFound()

        timing = "15d_before"
        if milestone.action_card_3d_id == action_card_id:
            timing = "3d_before"

        reminder = MilestoneReminder(
            student_id=student_id,
            milestone_id=milestone.id,
            timing=timing,
            sent_at=datetime.now(timezone.utc),
            action_items_checked=sorted(checked_indexes),
        )
        db.add(reminder)

    await db.flush()


def _build_card_response(card: ActionCard, checked_indexes: list[int]) -> dict:
    total = len(card.action_items) if card.action_items else 0
    done = len(checked_indexes)
    progress = round(done / total, 2) if total > 0 else 0

    return {
        "action_card": ActionCardResponse.model_validate(card),
        "checked_indexes": sorted(checked_indexes),
        "progress": progress,
    }
