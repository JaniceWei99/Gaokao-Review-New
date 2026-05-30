"""Dashboard service — aggregated data for the home page."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import StudentNotFound
from app.models.error_note import ErrorNote
from app.models.exam import Exam
from app.models.growth_record import GrowthRecord
from app.models.milestone import Milestone
from app.models.student import Student
from app.models.subscription import UserSubscription
from app.schemas.dashboard import (
    CountdownInfo,
    DashboardCountdowns,
    DashboardResponse,
    ErrorNotesSummary,
    SubscriptionSummary,
)
from app.schemas.milestone import ActionCardResponse, MilestoneResponse
from app.schemas.quote import TodayQuoteResponse
from app.services.milestone_service import _get_action_card, _adjust_dynamic_date
from app.services.quote_service import get_today_quote
from app.utils.date_utils import days_until

GAOKAO_DATES = {
    "gao1": date(2028, 6, 7),
    "gao2": date(2027, 6, 7),
    "gao3": date(2026, 6, 7),
}


def _get_student_subjects(student: Student) -> list[str]:
    subjects = []
    if student.selected_subject_1:
        subjects.append(student.selected_subject_1)
    if student.selected_subject_2:
        subjects.append(student.selected_subject_2)
    if student.selected_subject_3:
        subjects.append(student.selected_subject_3)
    return subjects


async def get_dashboard(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> DashboardResponse:
    """Build the aggregated dashboard response for a student."""
    student = await _get_student(student_id, user_id, db)

    today_quote = await get_today_quote(student_id, db)

    countdowns = await _build_countdowns(student_id, student, db)

    active_action_card = await _get_active_action_card(student_id, student, db)

    upcoming = await _get_upcoming_milestones(student_id, user_id, db)

    error_summary = await _get_error_notes_summary(student_id, db)

    growth_count = await _get_growth_records_count(student_id, db)

    subscription = await _get_subscription_summary(user_id, db)

    return DashboardResponse(
        today_quote=today_quote,
        countdowns=countdowns,
        active_action_card=active_action_card,
        upcoming_milestones=upcoming,
        error_notes_summary=error_summary,
        growth_records_count=growth_count,
        subscription=subscription,
    )


async def _get_student(
    student_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> Student:
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise StudentNotFound()
    return student


async def _build_countdowns(
    student_id: uuid.UUID, student: Student, db: AsyncSession
) -> DashboardCountdowns:
    nearest_exam = None
    gaokao = None
    today = date.today()

    from app.models.milestone import Milestone
    from sqlalchemy import or_

    query = select(Milestone).where(
        Milestone.applicable_grades.op("@>")(f'["{student.grade}"]'),
    )

    subjects = _get_student_subjects(student)
    if subjects:
        query = query.where(
            or_(
                Milestone.applicable_subjects.is_(None),
                Milestone.applicable_subjects.op("?|")(subjects),
            )
        )

    if student.district:
        query = query.where(
            or_(
                Milestone.applicable_districts.is_(None),
                Milestone.applicable_districts.op("@>")(f'["{student.district}"]'),
            )
        )

    if student.grade == "gao3" and not student.has_jan_english_exam:
        query = query.where(Milestone.requires_jan_english == False)

    result = await db.execute(query)
    milestones = list(result.scalars().all())

    for m in milestones:
        m._adjusted_event_date = _adjust_dynamic_date(m, today)

    future_milestones = [m for m in milestones if getattr(m, '_adjusted_event_date', m.event_date) >= today]
    future_milestones.sort(key=lambda m: getattr(m, '_adjusted_event_date', m.event_date))

    if future_milestones:
        nearest = future_milestones[0]
        adjusted_date = getattr(nearest, '_adjusted_event_date', nearest.event_date)
        days = days_until(adjusted_date)
        nearest_exam = CountdownInfo(title=nearest.title, days=days, date=adjusted_date)

    gaokao_date = GAOKAO_DATES.get(student.grade)
    if gaokao_date:
        gaokao_days = days_until(gaokao_date)
        gaokao = CountdownInfo(title="高考", days=gaokao_days, date=gaokao_date)

    return DashboardCountdowns(nearest_exam=nearest_exam, gaokao=gaokao)


async def _get_active_action_card(
    student_id: uuid.UUID, student: Student, db: AsyncSession
) -> ActionCardResponse | None:
    from app.models.milestone import Milestone
    from sqlalchemy import or_

    today = date.today()

    query = select(Milestone).where(
        Milestone.applicable_grades.op("@>")(f'["{student.grade}"]'),
    )

    subjects = _get_student_subjects(student)
    if subjects:
        query = query.where(
            or_(
                Milestone.applicable_subjects.is_(None),
                Milestone.applicable_subjects.op("?|")(subjects),
            )
        )

    if student.grade == "gao3" and not student.has_jan_english_exam:
        query = query.where(Milestone.requires_jan_english == False)

    result = await db.execute(query)
    milestones = list(result.scalars().all())

    for m in milestones:
        m._adjusted_event_date = _adjust_dynamic_date(m, today)

    future_milestones = [m for m in milestones if getattr(m, '_adjusted_event_date', m.event_date) >= today]
    future_milestones.sort(key=lambda m: getattr(m, '_adjusted_event_date', m.event_date))

    if not future_milestones:
        return None

    milestone = future_milestones[0]
    adjusted_date = getattr(milestone, '_adjusted_event_date', milestone.event_date)
    days = days_until(adjusted_date)

    if days <= 3 and milestone.action_card_3d_id:
        return await _get_action_card(milestone.action_card_3d_id, db)
    if days <= 15 and milestone.action_card_15d_id:
        return await _get_action_card(milestone.action_card_15d_id, db)

    return None


async def _get_upcoming_milestones(
    student_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> list[MilestoneResponse]:
    from app.services.milestone_service import list_milestones

    result = await list_milestones(student_id, user_id, db, current_only=True, limit=5)
    return result.milestones


async def _get_error_notes_summary(
    student_id: uuid.UUID, db: AsyncSession
) -> ErrorNotesSummary:
    total_result = await db.execute(
        select(func.count()).select_from(ErrorNote).where(
            ErrorNote.student_id == student_id
        )
    )
    total = total_result.scalar() or 0

    top_subject = None
    top_count = 0
    if total > 0:
        subject_result = await db.execute(
            select(ErrorNote.subject_id, func.count().label("cnt"))
            .where(ErrorNote.student_id == student_id)
            .group_by(ErrorNote.subject_id)
            .order_by(func.count().desc())
            .limit(1)
        )
        row = subject_result.first()
        if row:
            top_subject = row.subject_id
            top_count = row.cnt

    return ErrorNotesSummary(total=total, top_subject=top_subject, top_count=top_count)


async def _get_growth_records_count(
    student_id: uuid.UUID, db: AsyncSession
) -> int:
    result = await db.execute(
        select(func.count()).select_from(GrowthRecord).where(
            GrowthRecord.student_id == student_id
        )
    )
    return result.scalar() or 0


async def _get_subscription_summary(
    user_id: uuid.UUID, db: AsyncSession
) -> SubscriptionSummary:
    from app.middleware.permission import get_user_plan

    plan = "free"
    is_trial = False
    trial_days_remaining = None

    result = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == user_id, UserSubscription.plan != "free")
        .order_by(UserSubscription.created_at.desc())
        .limit(1)
    )
    sub = result.scalar_one_or_none()

    if sub:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        if sub.is_trial and sub.trial_expires_at and sub.trial_expires_at > now:
            plan = sub.plan
            is_trial = True
            trial_days_remaining = (sub.trial_expires_at - now).days
        elif sub.expires_at and sub.expires_at > now:
            plan = sub.plan

    return SubscriptionSummary(
        plan=plan,
        is_trial=is_trial,
        trial_days_remaining=trial_days_remaining,
    )
