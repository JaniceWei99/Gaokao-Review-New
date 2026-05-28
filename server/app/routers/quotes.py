"""Quotes router — daily quote, favorites, and share image."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.middleware.permission import require_standard
from app.schemas.quote import QuoteListResponse, TodayQuoteResponse
from app.services.cache_service import cache_get, cache_set
from app.services.quote_service import (
    favorite_quote,
    get_today_quote,
    list_favorites,
    unfavorite_quote,
)

router = APIRouter()


class ShareImageResponse(BaseModel):
    image_url: str


QUOTE_CACHE_TTL = 600


@router.get("/daily", response_model=TodayQuoteResponse)
async def daily_quote(
    student_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get today's quote for a student. Assigns one if not yet assigned."""
    cache_key = f"quote:daily:{student_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    result = await get_today_quote(student_id, db)

    await cache_set(cache_key, result.model_dump(), ttl=QUOTE_CACHE_TTL)

    return result


@router.post("/{quote_id}/favorite", status_code=204)
async def add_favorite(
    quote_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Add a quote to the user's favorites."""
    await favorite_quote(user_id, quote_id, db)


@router.delete("/{quote_id}/favorite", status_code=204)
async def remove_favorite(
    quote_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Remove a quote from the user's favorites."""
    await unfavorite_quote(user_id, quote_id, db)


@router.get("/favorites", response_model=QuoteListResponse)
async def list_my_favorites(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all favorited quotes for the authenticated user."""
    return await list_favorites(user_id, db)


@router.get("/{quote_id}/share-image", response_model=ShareImageResponse)
async def get_share_image(
    quote_id: uuid.UUID,
    plan: str = Depends(require_standard),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate or retrieve a share image for a quote. Requires standard plan."""
    from app.middleware.error_handler import ResourceNotFound
    from app.models.quote import DailyQuote
    from app.services.quote_image_service import generate_and_upload_quote_image
    from sqlalchemy import select

    cache_key = f"quote:share:{quote_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return ShareImageResponse(image_url=cached.get("image_url", ""))

    result = await db.execute(
        select(DailyQuote).where(DailyQuote.id == quote_id)
    )
    quote = result.scalar_one_or_none()
    if quote is None:
        raise ResourceNotFound()

    image_url = await generate_and_upload_quote_image(
        quote_id=quote.id,
        content=quote.content,
        author=quote.author,
    )

    await cache_set(cache_key, {"image_url": image_url}, ttl=3600)

    return ShareImageResponse(image_url=image_url)
