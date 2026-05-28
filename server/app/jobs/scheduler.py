"""APScheduler configuration and job definitions."""

from __future__ import annotations

import asyncio
import logging
from datetime import date

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

    This runs at 09:00 daily. For Phase 1, this only logs reminders.
    WeChat subscribe-message sending will be added in Phase 2.
    """
    logger.info("Starting reminder check job")
    today = date.today()

    async with async_session_factory() as db:
        from app.models.milestone import Milestone

        result = await db.execute(
            select(Milestone).where(Milestone.type == "system")
        )
        milestones = result.scalars().all()

        reminded = 0
        for m in milestones:
            days = (m.event_date - today).days
            if days in (15, 3):
                logger.info(
                    "Reminder: milestone '%s' is %d days away (date: %s)",
                    m.title,
                    days,
                    m.event_date,
                )
                reminded += 1

        logger.info("Reminder check complete: %d reminders", reminded)


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

    scheduler.start()
    logger.info("APScheduler started: daily_quote@08:00, reminder_check@09:00")


def stop_scheduler() -> None:
    """Shut down the scheduler."""
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("APScheduler stopped")
