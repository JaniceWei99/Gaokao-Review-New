"""Auth router — WeChat login and token refresh."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import WxLoginRequest, WxLoginResponse
from app.services.auth_service import wx_login

router = APIRouter()


@router.post("/wx-login", response_model=WxLoginResponse)
async def wechat_login(
    body: WxLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """WeChat mini-program login.

    The client calls wx.login() to get a temporary code, then sends it here.
    The server exchanges the code for an openid via WeChat API, finds or
    creates the user, and returns a JWT token.
    """
    return await wx_login(body.code, db)
