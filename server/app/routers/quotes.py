"""Quotes router — daily quote and favorites."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.schemas.quote import QuoteListResponse, TodayQuoteResponse
from app.services.quote_service import (
    favorite_quote,
    get_today_quote,
    list_favorites,
    unfavorite_quote,
)

router = APIRouter()


@router.get("/daily", response_model=TodayQuoteResponse)
async def daily_quote(
    student_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get today's quote for a student. Assigns one if not yet assigned."""
    return await get_today_quote(student_id, db)


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
