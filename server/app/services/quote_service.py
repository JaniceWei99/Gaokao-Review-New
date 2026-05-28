"""Quote service — daily quote assignment and favorites management."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import ResourceNotFound
from app.models.quote import DailyQuote, UserQuoteFavorite, UserQuoteHistory
from app.models.student import Student
from app.schemas.quote import QuoteListResponse, QuoteResponse, TodayQuoteResponse
from app.utils.date_utils import calculate_phase

logger = logging.getLogger(__name__)


async def get_today_quote(
    student_id: uuid.UUID, db: AsyncSession
) -> TodayQuoteResponse:
    """Get today's assigned quote for a student.

    If no quote has been assigned today, assign one on-the-fly.
    """
    today = date.today()

    result = await db.execute(
        select(UserQuoteHistory)
        .where(
            UserQuoteHistory.student_id == student_id,
            UserQuoteHistory.display_date == today,
        )
    )
    history = result.scalar_one_or_none()

    if history is not None:
        quote_result = await db.execute(
            select(DailyQuote).where(DailyQuote.id == history.quote_id)
        )
        quote = quote_result.scalar_one_or_none()
        if quote:
            is_fav = await _is_favorited(student_id, quote.id, db)
            return TodayQuoteResponse(
                quote=QuoteResponse.model_validate(quote),
                is_favorited=is_fav,
            )

    quote = await _assign_quote(student_id, today, db)
    is_fav = await _is_favorited(student_id, quote.id, db)
    return TodayQuoteResponse(
        quote=QuoteResponse.model_validate(quote),
        is_favorited=is_fav,
    )


async def _assign_quote(
    student_id: uuid.UUID, target_date: date, db: AsyncSession
) -> DailyQuote:
    """Assign a new quote to a student for a given date.

    Algorithm:
    1. Determine the student's grade and phase
    2. Find quotes matching grade + phase that haven't been shown recently
    3. If no candidates, reset history and try again
    4. Pick the first by display_order, then random
    """
    student = await db.get(Student, student_id)
    if student is None:
        raise ResourceNotFound()

    grade = student.grade or "gao1"
    phase = await _calculate_student_phase(student_id, student, db)

    shown_ids = await _get_shown_quote_ids(student_id, db)

    candidates = await _find_candidates(grade, phase, shown_ids, db)

    if not candidates:
        await _reset_quote_history(student_id, db)
        candidates = await _find_candidates(grade, phase, set(), db)

    if not candidates:
        candidates = await _find_candidates(grade, "all", set(), db)

    if not candidates:
        all_quotes_result = await db.execute(
            select(DailyQuote).where(DailyQuote.is_active == True).order_by(DailyQuote.display_order)
        )
        candidates = list(all_quotes_result.scalars().all())

    if not candidates:
        raise ResourceNotFound()

    quote = candidates[0]

    history = UserQuoteHistory(
        student_id=student_id,
        quote_id=quote.id,
        display_date=target_date,
    )
    db.add(history)
    await db.flush()

    return quote


async def _calculate_student_phase(
    student_id: uuid.UUID, student: Student, db: AsyncSession
) -> str:
    """Calculate the current exam phase for a student."""
    from app.models.milestone import Milestone

    result = await db.execute(
        select(Milestone.event_date)
        .where(
            Milestone.event_date >= date.today(),
            Milestone.type == "system",
        )
        .order_by(Milestone.event_date)
        .limit(1)
    )
    nearest_date = result.scalar_one_or_none()

    if nearest_date:
        days = (nearest_date - date.today()).days
        return calculate_phase(student.grade or "gao1", days)

    return "normal"


async def _get_shown_quote_ids(
    student_id: uuid.UUID, db: AsyncSession
) -> set[uuid.UUID]:
    """Get IDs of quotes already shown to this student."""
    result = await db.execute(
        select(UserQuoteHistory.quote_id).where(
            UserQuoteHistory.student_id == student_id
        )
    )
    return set(result.scalars().all())


async def _find_candidates(
    grade: str,
    phase: str,
    exclude_ids: set[uuid.UUID],
    db: AsyncSession,
) -> list[DailyQuote]:
    """Find matching quotes for a grade/phase, excluding already-shown IDs."""
    query = select(DailyQuote).where(DailyQuote.is_active == True)

    query = query.where(
        DailyQuote.applicable_grades.op("@>")(f'["{grade}"]')
    )

    if phase != "all":
        phase_filter = DailyQuote.applicable_phase.in_([phase, "all"])
        query = query.where(phase_filter)

    if exclude_ids:
        query = query.where(DailyQuote.id.notin_(exclude_ids))

    query = query.order_by(DailyQuote.display_order)

    result = await db.execute(query)
    return list(result.scalars().all())


async def _reset_quote_history(student_id: uuid.UUID, db: AsyncSession) -> None:
    """Delete all quote history for a student so quotes can cycle."""
    result = await db.execute(
        select(UserQuoteHistory).where(
            UserQuoteHistory.student_id == student_id
        )
    )
    for h in result.scalars().all():
        await db.delete(h)
    await db.flush()


async def _is_favorited(
    student_id: uuid.UUID, quote_id: uuid.UUID, db: AsyncSession
) -> bool:
    """Check if a quote is favorited by the student's user."""
    student = await db.get(Student, student_id)
    if student is None:
        return False

    result = await db.execute(
        select(UserQuoteFavorite).where(
            UserQuoteFavorite.user_id == student.user_id,
            UserQuoteFavorite.quote_id == quote_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def favorite_quote(
    user_id: uuid.UUID, quote_id: uuid.UUID, db: AsyncSession
) -> None:
    """Add a quote to the user's favorites."""
    result = await db.execute(
        select(UserQuoteFavorite).where(
            UserQuoteFavorite.user_id == user_id,
            UserQuoteFavorite.quote_id == quote_id,
        )
    )
    if result.scalar_one_or_none() is not None:
        return

    fav = UserQuoteFavorite(user_id=user_id, quote_id=quote_id)
    db.add(fav)
    await db.flush()


async def unfavorite_quote(
    user_id: uuid.UUID, quote_id: uuid.UUID, db: AsyncSession
) -> None:
    """Remove a quote from the user's favorites."""
    result = await db.execute(
        select(UserQuoteFavorite).where(
            UserQuoteFavorite.user_id == user_id,
            UserQuoteFavorite.quote_id == quote_id,
        )
    )
    fav = result.scalar_one_or_none()
    if fav:
        await db.delete(fav)
        await db.flush()


async def list_favorites(
    user_id: uuid.UUID, db: AsyncSession
) -> QuoteListResponse:
    """List all favorited quotes for a user."""
    result = await db.execute(
        select(DailyQuote)
        .join(UserQuoteFavorite, UserQuoteFavorite.quote_id == DailyQuote.id)
        .where(UserQuoteFavorite.user_id == user_id)
        .order_by(UserQuoteFavorite.created_at.desc())
    )
    quotes = result.scalars().all()
    return QuoteListResponse(quotes=[QuoteResponse.model_validate(q) for q in quotes])
