"""Authentication schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WxLoginRequest(BaseModel):
    """WeChat mini-program login request."""

    code: str = Field(..., description="wx.login获取的code")


class UserResponse(BaseModel):
    """Public user profile returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    openid: str
    nickname: str | None = None
    avatar_url: str | None = None
    created_at: datetime


class WxLoginResponse(BaseModel):
    """Response after successful WeChat login."""

    token: str
    user: UserResponse
    is_new_user: bool
