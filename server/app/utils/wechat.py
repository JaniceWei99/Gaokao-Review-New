"""WeChat API utilities — code2session, token management."""

from __future__ import annotations

import logging

import httpx
from app.config import settings

logger = logging.getLogger(__name__)

WX_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


async def code2session(code: str) -> dict:
    """Exchange a wx.login code for openid and session_key.

    Returns:
        dict with keys: openid, session_key, unionid (optional), errcode (on error)

    In development mode (wx_app_id empty), returns a mock response.
    """
    if not settings.wx_app_id or not settings.wx_app_secret:
        logger.info("WeChat mock mode: skipping code2session for code=%s", code[:8])
        return {
            "openid": f"mock_openid_{code}",
            "session_key": "mock_session_key",
        }

    params = {
        "appid": settings.wx_app_id,
        "secret": settings.wx_app_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(WX_CODE2SESSION_URL, params=params)
        data = resp.json()

    if "errcode" in data and data["errcode"] != 0:
        logger.error("WeChat code2session error: %s", data)
        raise ValueError(f"WeChat API error: {data.get('errmsg', 'unknown')}")

    return data
