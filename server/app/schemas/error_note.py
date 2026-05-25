"""Error-note schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorNoteCreate(BaseModel):
    """Payload for creating a new error note."""

    subject_id: str
    knowledge_node_id: uuid.UUID | None = None
    error_type: Literal[
        "careless", "concept_unclear", "method_unknown", "other"
    ] | None = None
    source: Literal[
        "monthly", "weekly", "homework", "mock", "other"
    ] | None = None
    note: str | None = Field(None, max_length=200)
    question_image_url: str
    correction_image_url: str | None = None


class ErrorNoteResponse(BaseModel):
    """Error note as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    subject_id: str
    knowledge_node_id: uuid.UUID | None
    error_type: str | None
    source: str | None
    question_image_url: str
    correction_image_url: str | None
    note: str | None
    created_at: datetime


class ErrorNoteStats(BaseModel):
    """Aggregate statistics for error notes."""

    total_count: int
    by_subject: dict[str, int]
    by_error_type: dict[str, int]


class ErrorNoteListResponse(BaseModel):
    """Paginated list of error notes with aggregate stats."""

    error_notes: list[ErrorNoteResponse]
    total: int
    page: int
    page_size: int
    stats: ErrorNoteStats
