"""Milestone service — filtering, countdown, custom milestones, and action cards."""

from __future__ import annotations

import logging
import uuid
from datetime import date

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import (
    CannotDeleteSystemMilestone,
    ResourceNotFound,
    StudentNotFound,
)
from app.models.action_card import ActionCard
from app.models.milestone import Milestone, MilestoneReminder
from app.models.student import Student
from app.schemas.milestone import (
    ActionCardResponse,
    MilestoneCreate,
    MilestoneListResponse,
    MilestoneResponse,
    MilestoneUpdate,
    NextMilestoneResponse,
)
from app.utils.date_utils import days_until

logger = logging.getLogger(__name__)


def _get_student_subjects(student: Student) -> list[str]:
    """Extract the student's elective subjects as a list."""
    subjects = []
    if student.selected_subject_1:
        subjects.append(student.selected_subject_1)
    if student.selected_subject_2:
        subjects.append(student.selected_subject_2)
    if student.selected_subject_3:
        subjects.append(student.selected_subject_3)
    return subjects


async def list_milestones(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    current_only: bool = False,
    limit: int | None = None,
) -> MilestoneListResponse:
    """List milestones applicable to a student.

    System milestones are filtered by grade/subjects/district/jan_english.
    Custom milestones (student_id = student_id) are always included.
    """
    student = await _get_student(student_id, user_id, db)
    subjects = _get_student_subjects(student)

    today = date.today()

    system_query = select(Milestone).where(
        Milestone.type == "system",
        Milestone.applicable_grades.op("@>")(f'["{student.grade}"]'),
    )

    if subjects:
        system_query = system_query.where(
            or_(
                Milestone.applicable_subjects.is_(None),
                Milestone.applicable_subjects.op("?|")(subjects),
            )
        )

    if student.district:
        system_query = system_query.where(
            or_(
                Milestone.applicable_districts.is_(None),
                Milestone.applicable_districts.op("@>")(f'["{student.district}"]'),
            )
        )

    if student.grade == "gao3" and not student.has_jan_english_exam:
        system_query = system_query.where(
            Milestone.requires_jan_english == False
        )

    if current_only:
        system_query = system_query.where(Milestone.event_date >= today)

    system_query = system_query.order_by(Milestone.event_date, Milestone.display_order)

    custom_query = select(Milestone).where(
        Milestone.type == "custom",
        Milestone.student_id == student_id,
    ).order_by(Milestone.event_date)

    if current_only:
        custom_query = custom_query.where(Milestone.event_date >= today)

    system_result = await db.execute(system_query)
    custom_result = await db.execute(custom_query)

    all_milestones = list(system_result.scalars().all()) + list(
        custom_result.scalars().all()
    )
    all_milestones.sort(key=lambda m: m.event_date)

    if limit:
        all_milestones = all_milestones[:limit]

    responses = []
    for m in all_milestones:
        resp = MilestoneResponse.model_validate(m)
        resp.days_remaining = days_until(m.event_date)
        resp.is_applicable = True
        responses.append(resp)

    return MilestoneListResponse(milestones=responses)


async def get_next_milestone(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> NextMilestoneResponse:
    """Get the next upcoming milestone for a student, with action card if available."""
    student = await _get_student(student_id, user_id, db)
    subjects = _get_student_subjects(student)
    today = date.today()

    system_query = select(Milestone).where(
        Milestone.type == "system",
        Milestone.event_date >= today,
        Milestone.applicable_grades.op("@>")(f'["{student.grade}"]'),
    )

    if subjects:
        system_query = system_query.where(
            or_(
                Milestone.applicable_subjects.is_(None),
                Milestone.applicable_subjects.op("?|")(subjects),
            )
        )

    if student.district:
        system_query = system_query.where(
            or_(
                Milestone.applicable_districts.is_(None),
                Milestone.applicable_districts.op("@>")(f'["{student.district}"]'),
            )
        )

    if student.grade == "gao3" and not student.has_jan_english_exam:
        system_query = system_query.where(Milestone.requires_jan_english == False)

    custom_query = select(Milestone).where(
        Milestone.type == "custom",
        Milestone.student_id == student_id,
        Milestone.event_date >= today,
    )

    system_result = await db.execute(system_query.order_by(Milestone.event_date).limit(1))
    custom_result = await db.execute(custom_query.order_by(Milestone.event_date).limit(1))

    system_ms = system_result.scalar_one_or_none()
    custom_ms = custom_result.scalar_one_or_none()

    milestone = None
    if system_ms and custom_ms:
        milestone = system_ms if system_ms.event_date <= custom_ms.event_date else custom_ms
    else:
        milestone = system_ms or custom_ms

    if milestone is None:
        return NextMilestoneResponse(
            next_milestone=None, days_remaining=None, next_action_card=None
        )

    days = days_until(milestone.event_date)
    resp = MilestoneResponse.model_validate(milestone)
    resp.days_remaining = days
    resp.is_applicable = True

    action_card = None
    if days <= 15 and milestone.action_card_15d_id:
        action_card = await _get_action_card(milestone.action_card_15d_id, db)
    elif days <= 3 and milestone.action_card_3d_id:
        action_card = await _get_action_card(milestone.action_card_3d_id, db)

    return NextMilestoneResponse(
        next_milestone=resp,
        days_remaining=days,
        next_action_card=action_card,
    )


async def create_custom_milestone(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    data: MilestoneCreate,
    db: AsyncSession,
) -> MilestoneResponse:
    """Create a custom milestone for a student."""
    await _get_student(student_id, user_id, db)

    milestone = Milestone(
        type="custom",
        student_id=student_id,
        title=data.title,
        description=data.description,
        event_date=data.event_date,
        event_end_date=data.event_end_date,
        category=data.category,
        applicable_grades=[],
        requires_jan_english=False,
        is_dynamic_date=False,
    )
    db.add(milestone)
    await db.flush()

    resp = MilestoneResponse.model_validate(milestone)
    resp.days_remaining = days_until(milestone.event_date)
    resp.is_applicable = True
    return resp


async def update_custom_milestone(
    milestone_id: uuid.UUID,
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    data: MilestoneUpdate,
    db: AsyncSession,
) -> MilestoneResponse:
    """Update a custom milestone."""
    await _get_student(student_id, user_id, db)

    result = await db.execute(
        select(Milestone).where(
            Milestone.id == milestone_id,
            Milestone.student_id == student_id,
            Milestone.type == "custom",
        )
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        raise ResourceNotFound()

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(milestone, field, value)

    await db.flush()

    resp = MilestoneResponse.model_validate(milestone)
    resp.days_remaining = days_until(milestone.event_date)
    resp.is_applicable = True
    return resp


async def delete_custom_milestone(
    milestone_id: uuid.UUID,
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Delete a custom milestone. System milestones cannot be deleted."""
    result = await db.execute(
        select(Milestone).where(
            Milestone.id == milestone_id,
            Milestone.student_id == student_id,
        )
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        raise ResourceNotFound()

    if milestone.type == "system":
        raise CannotDeleteSystemMilestone()

    await db.delete(milestone)
    await db.flush()


async def _get_student(
    student_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> Student:
    """Get a student, verifying ownership."""
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise StudentNotFound()
    return student


async def _get_action_card(
    action_card_id: uuid.UUID, db: AsyncSession
) -> ActionCardResponse | None:
    """Get an action card by ID."""
    result = await db.execute(
        select(ActionCard).where(ActionCard.id == action_card_id)
    )
    card = result.scalar_one_or_none()
    if card is None:
        return None
    return ActionCardResponse.model_validate(card)
