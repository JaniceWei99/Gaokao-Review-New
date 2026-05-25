"""Exam and score schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExamScoreInput(BaseModel):
    """Single subject score submitted when creating an exam."""

    subject_id: str
    score: float = Field(..., ge=0)
    max_score: float = Field(..., gt=0, le=300)

    @model_validator(mode="after")
    def _validate_score_bounds(self) -> ExamScoreInput:
        if self.max_score < 10:
            raise ValueError(
                "满分不能低于10分 (max_score must be >= 10)"
            )
        if self.score > self.max_score:
            raise ValueError(
                f"得分({self.score})不能超过满分({self.max_score}) "
                f"(score must be <= max_score)"
            )
        return self


class ExamCreate(BaseModel):
    """Payload for recording a new exam with scores."""

    name: str = Field(..., max_length=50)
    exam_type: Literal[
        "monthly", "midterm", "final",
        "mock1", "mock2", "mock3", "other",
    ]
    exam_date: date
    scores: list[ExamScoreInput]


class ExamScoreResponse(BaseModel):
    """Individual subject score as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: str
    score: float
    max_score: float
    score_rate: float | None


class ExamResponse(BaseModel):
    """Exam record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    name: str
    exam_type: str
    exam_date: date
    scores: list[ExamScoreResponse] = []
    created_at: datetime


class ProgressDetected(BaseModel):
    """Describes progress detected in a specific subject after an exam."""

    subject_id: str
    subject_name: str
    previous_rate: float
    current_rate: float
    improvement: float


class ExamCreateResponse(BaseModel):
    """Response after creating an exam, optionally includes progress info."""

    exam: ExamResponse
    progress_detected: list[ProgressDetected] | None = None


class ExamListResponse(BaseModel):
    """Wrapper for a list of exams."""

    exams: list[ExamResponse]


class TrendPoint(BaseModel):
    """A single data point in an exam score trend."""

    exam_name: str
    exam_date: date
    score: float
    max_score: float
    score_rate: float


class ExamTrendResponse(BaseModel):
    """Score trend analysis for a subject."""

    trend: list[TrendPoint]
    overall_trend: Literal["up", "down", "stable"]
    best_rate: float | None
    latest_rate: float | None


class LastMaxScoresResponse(BaseModel):
    """Most recent max_score for each subject (used as defaults in the UI)."""

    last_max_scores: dict[str, float]
