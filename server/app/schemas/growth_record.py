"""Growth-record schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.quote import QuoteResponse


class GrowthRecordCreate(BaseModel):
    """Payload for creating a new growth record."""

    record_type: Literal[
        "award", "progress", "performance", "breakthrough", "memo"
    ]
    title: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=500)
    record_date: date
    category: Literal[
        "academic_competition",
        "sports",
        "comprehensive",
        "social_practice",
        "other",
    ] | None = None
    awarding_body: str | None = Field(None, max_length=100)
    image_url: str | None = None
    auto_generated: bool = False


class GrowthRecordResponse(BaseModel):
    """Growth record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    record_type: str
    title: str
    description: str | None
    record_date: date
    category: str | None
    awarding_body: str | None
    image_url: str | None
    auto_generated: bool
    linked_quote_id: uuid.UUID | None
    created_at: datetime


class GrowthRecordCreateResponse(BaseModel):
    """Response after creating a growth record, optionally with a matched quote."""

    growth_record: GrowthRecordResponse
    matched_quote: QuoteResponse | None = None


class GrowthRecordListResponse(BaseModel):
    """Paginated list of growth records grouped by school year."""

    growth_records: list[GrowthRecordResponse]
    total: int
    by_school_year: dict[str, list[GrowthRecordResponse]]
