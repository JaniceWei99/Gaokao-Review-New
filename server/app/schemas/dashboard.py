"""Dashboard schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.schemas.milestone import ActionCardResponse, MilestoneResponse
from app.schemas.quote import TodayQuoteResponse


class CountdownInfo(BaseModel):
    """A single countdown item (e.g. days until an exam)."""

    title: str
    days: int
    date: date


class DashboardCountdowns(BaseModel):
    """Countdown timers shown on the dashboard."""

    nearest_exam: CountdownInfo | None
    gaokao: CountdownInfo | None  # Only populated for gao3 students


class ErrorNotesSummary(BaseModel):
    """Brief error-notes overview for the dashboard."""

    total: int
    top_subject: str | None
    top_count: int


class SubscriptionSummary(BaseModel):
    """Brief subscription overview for the dashboard."""

    plan: str
    is_trial: bool
    trial_days_remaining: int | None


class DashboardResponse(BaseModel):
    """Aggregated dashboard data returned to the client."""

    today_quote: TodayQuoteResponse
    countdowns: DashboardCountdowns
    active_action_card: ActionCardResponse | None
    upcoming_milestones: list[MilestoneResponse]
    error_notes_summary: ErrorNotesSummary
    growth_records_count: int
    subscription: SubscriptionSummary
