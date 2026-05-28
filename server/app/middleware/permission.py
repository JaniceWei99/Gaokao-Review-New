"""Subscription permission checking dependency for FastAPI."""

import uuid
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.middleware.error_handler import (
    FeatureRequiresPremium,
    FeatureRequiresStandard,
    FreeLimitErrorNotes,
    FreeLimitExams,
    FreeLimitGrowth,
)


async def get_user_plan(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Get the current active plan for a user. Returns 'free', 'standard', or 'premium'."""
    from app.models.subscription import UserSubscription

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(UserSubscription)
        .where(
            UserSubscription.user_id == user_id,
        )
        .order_by(UserSubscription.created_at.desc())
        .limit(1)
    )
    sub = result.scalar_one_or_none()

    if sub is None:
        return "free"

    if hasattr(sub, "payment_status") and sub.payment_status == "pending":
        prev_result = await db.execute(
            select(UserSubscription)
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.id != sub.id,
            )
            .order_by(UserSubscription.created_at.desc())
            .limit(1)
        )
        prev_sub = prev_result.scalar_one_or_none()
        if prev_sub:
            if prev_sub.is_trial and prev_sub.trial_expires_at and prev_sub.trial_expires_at < now:
                return "free"
            if not prev_sub.is_trial and prev_sub.expires_at and prev_sub.expires_at < now:
                return "free"
            return prev_sub.plan or "free"
        return "free"

    if sub.is_trial and sub.trial_expires_at and sub.trial_expires_at < now:
        return "free"

    if not sub.is_trial and sub.expires_at and sub.expires_at < now:
        return "free"

    return sub.plan or "free"


def require_standard(plan: str = Depends(get_user_plan)) -> str:
    """Require at least standard plan."""
    if plan == "free":
        raise FeatureRequiresStandard()
    return plan


def require_premium(plan: str = Depends(get_user_plan)) -> str:
    """Require premium plan."""
    if plan != "premium":
        raise FeatureRequiresPremium()
    return plan


async def check_error_note_limit(
    student_id: uuid.UUID,
    db: AsyncSession,
    plan: str,
) -> None:
    """Check if the user can add more error notes under their plan."""
    if plan != "free":
        return
    from app.models.error_note import ErrorNote

    result = await db.execute(
        select(func.count())
        .select_from(ErrorNote)
        .where(ErrorNote.student_id == student_id)
    )
    count = result.scalar() or 0
    if count >= 10:
        raise FreeLimitErrorNotes()


async def check_growth_record_limit(
    student_id: uuid.UUID,
    db: AsyncSession,
    plan: str,
) -> None:
    """Check if the user can add more growth records under their plan."""
    if plan != "free":
        return
    from app.models.growth_record import GrowthRecord

    result = await db.execute(
        select(func.count())
        .select_from(GrowthRecord)
        .where(GrowthRecord.student_id == student_id)
    )
    count = result.scalar() or 0
    if count >= 5:
        raise FreeLimitGrowth()


async def check_exam_limit(
    student_id: uuid.UUID,
    db: AsyncSession,
    plan: str,
) -> None:
    """Check if the user can add more exam records under their plan."""
    if plan != "free":
        return
    from app.models.exam import Exam

    result = await db.execute(
        select(func.count())
        .select_from(Exam)
        .where(Exam.student_id == student_id)
    )
    count = result.scalar() or 0
    if count >= 3:
        raise FreeLimitExams()
