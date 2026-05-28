"""Subscription schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SubscriptionLimits(BaseModel):
    """Feature limits and usage for the current subscription plan."""

    error_notes_max: int | None  # None = unlimited
    error_notes_used: int
    growth_records_max: int | None
    growth_records_used: int
    can_expand_knowledge_l3: bool
    can_share_quote_image: bool
    can_use_widget: bool
    can_export_growth: bool
    can_view_exam_trend: bool
    has_action_cards: bool
    has_ai_chat: bool = False
    has_ai_suggestions: bool = False
    has_ai_personalized_quote: bool = False
    has_ai_error_classify: bool = False
    has_ai_monthly_report: bool = False


class SubscriptionResponse(BaseModel):
    """Current subscription state for a user."""

    plan: str
    billing_type: str | None
    expires_at: datetime | None
    is_trial: bool
    trial_expires_at: datetime | None
    limits: SubscriptionLimits


class UpgradeRequest(BaseModel):
    """Payload for upgrading to a paid plan."""

    plan: Literal["standard", "premium"]
    billing_type: Literal["monthly", "yearly", "lifetime_high_school"]
