"""Pydantic v2 request / response schemas for the Shanghai Gaokao Companion API."""

from app.schemas.auth import UserResponse, WxLoginRequest, WxLoginResponse
from app.schemas.dashboard import (
    CountdownInfo,
    DashboardCountdowns,
    DashboardResponse,
    ErrorNotesSummary,
    SubscriptionSummary,
)
from app.schemas.error_note import (
    ErrorNoteCreate,
    ErrorNoteListResponse,
    ErrorNoteResponse,
    ErrorNoteStats,
)
from app.schemas.exam import (
    ExamCreate,
    ExamCreateResponse,
    ExamListResponse,
    ExamResponse,
    ExamScoreInput,
    ExamScoreResponse,
    ExamTrendResponse,
    LastMaxScoresResponse,
    ProgressDetected,
    TrendPoint,
)
from app.schemas.growth_record import (
    GrowthRecordCreate,
    GrowthRecordCreateResponse,
    GrowthRecordListResponse,
    GrowthRecordResponse,
)
from app.schemas.milestone import (
    ActionCardResponse,
    MilestoneCreate,
    MilestoneListResponse,
    MilestoneResponse,
    MilestoneUpdate,
    NextMilestoneResponse,
    ReminderActionsUpdate,
    ReminderOpenRequest,
)
from app.schemas.quote import QuoteListResponse, QuoteResponse, TodayQuoteResponse
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate
from app.schemas.subscription import (
    SubscriptionLimits,
    SubscriptionResponse,
    UpgradeRequest,
)

__all__ = [
    # auth
    "WxLoginRequest",
    "WxLoginResponse",
    "UserResponse",
    # student
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    # milestone
    "MilestoneResponse",
    "MilestoneCreate",
    "MilestoneUpdate",
    "ActionCardResponse",
    "ReminderOpenRequest",
    "ReminderActionsUpdate",
    "MilestoneListResponse",
    "NextMilestoneResponse",
    # quote
    "QuoteResponse",
    "TodayQuoteResponse",
    "QuoteListResponse",
    # exam
    "ExamScoreInput",
    "ExamCreate",
    "ExamScoreResponse",
    "ExamResponse",
    "ProgressDetected",
    "ExamCreateResponse",
    "ExamListResponse",
    "TrendPoint",
    "ExamTrendResponse",
    "LastMaxScoresResponse",
    # error_note
    "ErrorNoteCreate",
    "ErrorNoteResponse",
    "ErrorNoteStats",
    "ErrorNoteListResponse",
    # growth_record
    "GrowthRecordCreate",
    "GrowthRecordResponse",
    "GrowthRecordCreateResponse",
    "GrowthRecordListResponse",
    # subscription
    "SubscriptionResponse",
    "SubscriptionLimits",
    "UpgradeRequest",
    # dashboard
    "CountdownInfo",
    "DashboardCountdowns",
    "ErrorNotesSummary",
    "SubscriptionSummary",
    "DashboardResponse",
]
