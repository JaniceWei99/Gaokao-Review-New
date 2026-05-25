"""Milestone and action-card schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MilestoneResponse(BaseModel):
    """Milestone event as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    title: str
    description: str | None
    event_date: date
    event_end_date: date | None
    category: str
    applicable_grades: list[str]
    requires_jan_english: bool
    is_dynamic_date: bool
    display_order: int
    # Computed fields – not stored in DB, populated by the service layer
    days_remaining: int | None = None
    is_applicable: bool | None = None


class MilestoneCreate(BaseModel):
    """Payload for creating a custom milestone."""

    title: str = Field(..., max_length=50)
    event_date: date
    event_end_date: date | None = None
    category: Literal["custom"] = "custom"
    description: str | None = Field(None, max_length=200)


class MilestoneUpdate(BaseModel):
    """Payload for updating a custom milestone (all fields optional)."""

    title: str | None = Field(None, max_length=50)
    event_date: date | None = None
    event_end_date: date | None = None
    description: str | None = None


class ActionCardResponse(BaseModel):
    """Pre-defined action card tied to a milestone category + timing."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    milestone_category: str
    timing: str
    title: str
    description: str | None
    action_items: list[dict]  # list of action-item objects
    footer_tip: str | None
    quote_category: str | None


class ReminderOpenRequest(BaseModel):
    """Body for marking a milestone reminder as opened (no fields needed)."""

    pass  # no body needed


class ReminderActionsUpdate(BaseModel):
    """Body for updating which action items have been checked."""

    checked_indexes: list[int]


class MilestoneListResponse(BaseModel):
    """Wrapper for a list of milestones."""

    milestones: list[MilestoneResponse]


class NextMilestoneResponse(BaseModel):
    """Response for the "next milestone" endpoint."""

    next_milestone: MilestoneResponse | None
    days_remaining: int | None
    next_action_card: ActionCardResponse | None
