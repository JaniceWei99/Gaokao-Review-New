"""APScheduler configuration and job definitions."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.quote import DailyQuote, UserQuoteHistory
from app.models.student import Student

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None


async def assign_daily_quotes_job() -> None:
    """Pre-assign today's quote for all active students.

    This runs at 08:00 daily. Students who already have a quote assigned
    today are skipped.
    """
    logger.info("Starting daily quote assignment job")
    today = date.today()

    async with async_session_factory() as db:
        result = await db.execute(select(Student))
        students = result.scalars().all()

        assigned = 0
        for student in students:
            existing = await db.execute(
                select(UserQuoteHistory).where(
                    UserQuoteHistory.student_id == student.id,
                    UserQuoteHistory.display_date == today,
                )
            )
            if existing.scalar_one_or_none():
                continue

            try:
                from app.services.quote_service import get_today_quote

                await get_today_quote(student.id, db)
                assigned += 1
            except Exception as exc:
                logger.warning(
                    "Failed to assign quote for student %s: %s", student.id, exc
                )

        await db.commit()
        logger.info("Daily quote assignment complete: %d students", assigned)


async def reminder_check_job() -> None:
    """Check for upcoming milestones and send reminders.

    This runs at 09:00 daily. Sends WeChat subscribe messages for
    milestones 15d / 3d away.
    """
    logger.info("Starting reminder check job")
    today = date.today()

    async with async_session_factory() as db:
        from app.models.milestone import Milestone, MilestoneReminder
        from app.models.student import Student
        from app.models.user import User

        result = await db.execute(
            select(Milestone).where(Milestone.type == "system")
        )
        milestones = result.scalars().all()

        reminded = 0
        for m in milestones:
            days = (m.event_date - today).days
            if days not in (15, 3):
                continue

            timing = "15d_before" if days == 15 else "3d_before"

            applicable_grades = m.applicable_grades or []
            student_query = select(Student)
            if applicable_grades:
                student_query = student_query.where(
                    Student.grade.in_(applicable_grades)
                )
            student_result = await db.execute(student_query)
            students = student_result.scalars().all()

            for student in students:
                existing = await db.execute(
                    select(MilestoneReminder).where(
                        MilestoneReminder.student_id == student.id,
                        MilestoneReminder.milestone_id == m.id,
                        MilestoneReminder.timing == timing,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                reminder = MilestoneReminder(
                    student_id=student.id,
                    milestone_id=m.id,
                    timing=timing,
                    sent_at=datetime.now(timezone.utc),
                )
                db.add(reminder)

                try:
                    user = await db.get(User, student.user_id)
                    if user and user.openid:
                        await _send_milestone_subscribe_message(
                            openid=user.openid,
                            milestone_title=m.title,
                            days_remaining=days,
                            milestone_id=str(m.id),
                            timing=timing,
                        )
                except Exception as exc:
                    logger.warning(
                        "Failed to send reminder to student %s: %s",
                        student.id, exc,
                    )

                reminded += 1

        await db.commit()
        logger.info("Reminder check complete: %d reminders sent", reminded)


async def _send_milestone_subscribe_message(
    openid: str,
    milestone_title: str,
    days_remaining: int,
    milestone_id: str,
    timing: str,
) -> None:
    """Send a WeChat subscribe message for milestone reminder."""
    from app.config import settings

    if not settings.wx_app_id:
        logger.info("Mock subscribe message: %s is %d days away", milestone_title, days_remaining)
        return

    try:
        import httpx

        access_token = await _get_access_token()
        if not access_token:
            return

        url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}"
        body = {
            "touser": openid,
            "template_id": settings.wx_subscribe_milestone_template_id if hasattr(settings, 'wx_subscribe_milestone_template_id') else "",
            "page": f"pages/milestones/action-card?id={milestone_id}&timing={timing}",
            "data": {
                "thing1": {"value": milestone_title[:20]},
                "number2": {"value": str(days_remaining)},
                "thing3": {"value": "查看家长准备清单"[:20]},
            },
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=body)
            result = resp.json()

        if result.get("errcode", 0) != 0:
            logger.warning("Subscribe message send failed: %s", result)
    except Exception as exc:
        logger.warning("Failed to send subscribe message: %s", exc)


async def _get_access_token() -> str | None:
    """Get WeChat access token for subscribe messages."""
    from app.config import settings

    if not settings.wx_app_id or not settings.wx_app_secret:
        return None

    try:
        import httpx

        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": settings.wx_app_id,
            "secret": settings.wx_app_secret,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        return data.get("access_token")
    except Exception as exc:
        logger.warning("Failed to get access token: %s", exc)
        return None


async def trial_expiry_check_job() -> None:
    """Check for expired trials and log them.

    This runs at 10:00 daily. Trials that have expired are logged;
    the permission middleware already handles the downgrade.
    """
    logger.info("Starting trial expiry check job")

    async with async_session_factory() as db:
        from app.models.subscription import UserSubscription

        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(UserSubscription).where(
                UserSubscription.is_trial == True,
                UserSubscription.trial_expires_at < now,
            )
        )
        expired_trials = result.scalars().all()

        for trial in expired_trials:
            logger.info(
                "Trial expired for user %s (expired at %s)",
                trial.user_id,
                trial.trial_expires_at,
            )

        await db.commit()
        logger.info("Trial expiry check complete: %d expired trials", len(expired_trials))


def start_scheduler() -> None:
    """Initialize and start the APScheduler."""
    global scheduler

    if scheduler is not None:
        return

    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        assign_daily_quotes_job,
        "cron",
        hour=8,
        minute=0,
        id="daily_quote",
        replace_existing=True,
    )

    scheduler.add_job(
        reminder_check_job,
        "cron",
        hour=9,
        minute=0,
        id="reminder_check",
        replace_existing=True,
    )

    scheduler.add_job(
        trial_expiry_check_job,
        "cron",
        hour=10,
        minute=0,
        id="trial_expiry_check",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("APScheduler started: daily_quote@08:00, reminder_check@09:00, trial_expiry@10:00")


def stop_scheduler() -> None:
    """Shut down the scheduler."""
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("APScheduler stopped")
