"""Schemas for AI chat endpoints."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="User message")
    session_id: uuid.UUID | None = Field(None, description="Existing session ID to continue")


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    created_date: datetime.date
    messages: list[ChatMessageResponse]
    remaining_chats: int

    model_config = {"from_attributes": True}


class ChatListResponse(BaseModel):
    sessions: list[ChatSessionSummary]
    total: int


class ChatSessionSummary(BaseModel):
    id: uuid.UUID
    title: str | None
    created_date: datetime.date
    last_message: str | None
    message_count: int

    model_config = {"from_attributes": True}
