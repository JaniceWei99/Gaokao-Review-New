"""Subscription service — plan management, trial, upgrade, and limits."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import AppException, InvalidParams
from app.models.error_note import ErrorNote
from app.models.exam import Exam
from app.models.growth_record import GrowthRecord
from app.models.student import Student
from app.models.subscription import UserSubscription
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionLimits,
    SubscriptionResponse,
    UpgradeRequest,
)
from app.services.payment_service import PRICING_YUAN, create_jsapi_order

logger = logging.getLogger(__name__)

TRIAL_DAYS = 7


async def get_subscription_status(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> SubscriptionResponse:
    """Get the current subscription status with usage limits."""
    plan, billing_type, expires_at, is_trial, trial_expires_at = (
        await _get_active_plan(user_id, db)
    )

    student = await _get_primary_student(user_id, db)
    limits = await _build_limits(student, plan, db) if student else _empty_limits(plan)

    return SubscriptionResponse(
        plan=plan,
        billing_type=billing_type,
        expires_at=expires_at,
        is_trial=is_trial,
        trial_expires_at=trial_expires_at,
        limits=limits,
    )


async def start_trial(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Start a 7-day free trial of the standard plan for a new user."""
    existing = await db.execute(
        select(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.is_trial == True,
        )
    )
    if existing.scalar_one_or_none():
        return

    now = datetime.now(timezone.utc)
    trial_expires = now + timedelta(days=TRIAL_DAYS)

    sub = UserSubscription(
        user_id=user_id,
        plan="standard",
        billing_type=None,
        price_paid=0,
        started_at=now,
        expires_at=trial_expires,
        is_trial=True,
        trial_expires_at=trial_expires,
        auto_renew=False,
    )
    db.add(sub)
    await db.flush()
    logger.info("Started 7-day trial for user %s", user_id)


async def upgrade_subscription(
    user_id: uuid.UUID,
    data: UpgradeRequest,
    db: AsyncSession,
) -> dict:
    """Initiate a subscription upgrade by creating a WeChat Pay order.

    Returns payment parameters for wx.requestPayment().
    """
    plan, _, _, is_trial, _ = await _get_active_plan(user_id, db)

    if data.plan == "standard" and plan == "premium":
        raise InvalidParams("无法从高级版降级到标准版")

    if data.plan == plan and not is_trial:
        raise InvalidParams("当前已是该版本")

    price = PRICING_YUAN.get((data.plan, data.billing_type))
    if price is None:
        raise InvalidParams("无效的套餐组合")

    user = await db.get(User, user_id)
    if user is None:
        raise InvalidParams("用户不存在")

    out_trade_no = f"sub_{user_id.hex[:12]}_{int(datetime.now(timezone.utc).timestamp())}"

    pay_params = await create_jsapi_order(
        user_id=user_id,
        openid=user.openid,
        plan=data.plan,
        billing_type=data.billing_type,
        out_trade_no=out_trade_no,
    )

    pending = UserSubscription(
        user_id=user_id,
        plan=data.plan,
        billing_type=data.billing_type,
        price_paid=price,
        started_at=datetime.now(timezone.utc),
        expires_at=_calculate_expires(data.billing_type),
        is_trial=False,
        auto_renew=data.billing_type != "lifetime_high_school",
    )
    pending.out_trade_no = out_trade_no
    pending.payment_status = "pending"
    db.add(pending)
    await db.flush()

    return pay_params


async def handle_payment_callback(
    out_trade_no: str,
    trade_state: str,
    db: AsyncSession,
) -> None:
    """Handle WeChat Pay callback — activate subscription on successful payment."""
    result = await db.execute(
        select(UserSubscription).where(
            UserSubscription.out_trade_no == out_trade_no,
        )
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        logger.warning("Payment callback for unknown order: %s", out_trade_no)
        return

    if trade_state == "SUCCESS":
        sub.payment_status = "paid"
        sub.started_at = datetime.now(timezone.utc)
        sub.expires_at = _calculate_expires(sub.billing_type)

        await db.execute(
            select(UserSubscription).where(
                UserSubscription.user_id == sub.user_id,
                UserSubscription.id != sub.id,
                UserSubscription.is_trial == True,
            )
        )
        await db.flush()
        logger.info("Subscription activated for user %s, plan=%s", sub.user_id, sub.plan)
    else:
        sub.payment_status = "failed"
        await db.flush()
        logger.info("Payment failed for order %s, state=%s", out_trade_no, trade_state)


async def _get_active_plan(
    user_id: uuid.UUID, db: AsyncSession
) -> tuple[str, str | None, datetime | None, bool, datetime | None]:
    """Return (plan, billing_type, expires_at, is_trial, trial_expires_at)."""
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
        return ("free", None, None, False, None)

    if sub.is_trial and sub.trial_expires_at and sub.trial_expires_at < now:
        return ("free", None, None, False, None)

    if not sub.is_trial and sub.expires_at and sub.expires_at < now:
        return ("free", None, None, False, None)

    if hasattr(sub, "payment_status") and sub.payment_status == "pending":
        prev_result = await db.execute(
            select(UserSubscription)
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.id != sub.id,
                UserSubscription.payment_status != "pending",
            )
            .order_by(UserSubscription.created_at.desc())
            .limit(1)
        )
        prev_sub = prev_result.scalar_one_or_none()
        if prev_sub and not (prev_sub.is_trial and prev_sub.trial_expires_at and prev_sub.trial_expires_at < now):
            if not (prev_sub.expires_at and prev_sub.expires_at < now):
                return (
                    prev_sub.plan or "free",
                    prev_sub.billing_type,
                    prev_sub.expires_at,
                    prev_sub.is_trial,
                    prev_sub.trial_expires_at,
                )
        return ("free", None, None, False, None)

    return (
        sub.plan or "free",
        sub.billing_type,
        sub.expires_at,
        sub.is_trial,
        sub.trial_expires_at,
    )


async def _build_limits(
    student: Student, plan: str, db: AsyncSession
) -> SubscriptionLimits:
    """Build the limits object based on plan and current usage."""
    error_count = await _count_records(ErrorNote, ErrorNote.student_id, student.id, db)
    growth_count = await _count_records(GrowthRecord, GrowthRecord.student_id, student.id, db)

    if plan == "free":
        return SubscriptionLimits(
            error_notes_max=10,
            error_notes_used=error_count,
            growth_records_max=5,
            growth_records_used=growth_count,
            can_expand_knowledge_l3=False,
            can_share_quote_image=False,
            can_use_widget=False,
            can_export_growth=False,
            can_view_exam_trend=False,
            has_action_cards=False,
        )
    elif plan == "standard":
        return SubscriptionLimits(
            error_notes_max=None,
            error_notes_used=error_count,
            growth_records_max=None,
            growth_records_used=growth_count,
            can_expand_knowledge_l3=True,
            can_share_quote_image=True,
            can_use_widget=True,
            can_export_growth=True,
            can_view_exam_trend=True,
            has_action_cards=True,
        )
    else:
        return SubscriptionLimits(
            error_notes_max=None,
            error_notes_used=error_count,
            growth_records_max=None,
            growth_records_used=growth_count,
            can_expand_knowledge_l3=True,
            can_share_quote_image=True,
            can_use_widget=True,
            can_export_growth=True,
            can_view_exam_trend=True,
            has_action_cards=True,
        )


def _empty_limits(plan: str) -> SubscriptionLimits:
    """Return limits when no student is found."""
    if plan == "free":
        return SubscriptionLimits(
            error_notes_max=10, error_notes_used=0,
            growth_records_max=5, growth_records_used=0,
            can_expand_knowledge_l3=False, can_share_quote_image=False,
            can_use_widget=False, can_export_growth=False,
            can_view_exam_trend=False, has_action_cards=False,
        )
    return SubscriptionLimits(
        error_notes_max=None, error_notes_used=0,
        growth_records_max=None, growth_records_used=0,
        can_expand_knowledge_l3=True, can_share_quote_image=True,
        can_use_widget=True, can_export_growth=True,
        can_view_exam_trend=True, has_action_cards=True,
    )


async def _count_records(model, field, student_id: uuid.UUID, db: AsyncSession) -> int:
    """Count records for a student in a given model."""
    result = await db.execute(
        select(func.count()).select_from(model).where(field == student_id)
    )
    return result.scalar() or 0


async def _get_primary_student(
    user_id: uuid.UUID, db: AsyncSession
) -> Student | None:
    """Get the first student for a user."""
    result = await db.execute(
        select(Student).where(Student.user_id == user_id).limit(1)
    )
    return result.scalar_one_or_none()


def _calculate_expires(billing_type: str | None) -> datetime:
    """Calculate the expiration datetime based on billing type."""
    now = datetime.now(timezone.utc)
    if billing_type == "monthly":
        return now + relativedelta(months=1)
    elif billing_type == "yearly":
        return now + relativedelta(years=1)
    elif billing_type == "lifetime_high_school":
        return now + relativedelta(years=3)
    return now + relativedelta(months=1)
