"""Quote schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class QuoteResponse(BaseModel):
    """Daily inspirational quote as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    author: str | None
    category: str
    applicable_grades: list[str]
    applicable_phase: str


class TodayQuoteResponse(BaseModel):
    """Today's quote together with the user's favorite status."""

    quote: QuoteResponse
    is_favorited: bool


class QuoteListResponse(BaseModel):
    """Wrapper for a list of quotes."""

    quotes: list[QuoteResponse]
