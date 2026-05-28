"""Authentication service — WeChat login + JWT token management."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import create_access_token
from app.middleware.error_handler import InternalError, Unauthorized
from app.models.user import User
from app.schemas.auth import UserResponse, WxLoginResponse
from app.utils.wechat import code2session

logger = logging.getLogger(__name__)


async def wx_login(code: str, db: AsyncSession) -> WxLoginResponse:
    """Process a WeChat mini-program login.

    1. Exchange code for openid via WeChat API
    2. Find or create the User record
    3. Generate a JWT token
    """
    try:
        wx_data = await code2session(code)
    except Exception as exc:
        logger.error("WeChat code2session failed: %s", exc)
        raise InternalError(detail="微信登录服务暂时不可用") from exc

    openid = wx_data.get("openid")
    if not openid:
        raise Unauthorized()

    union_id = wx_data.get("unionid")

    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()

    is_new_user = user is None

    if user is None:
        user = User(
            openid=openid,
            union_id=union_id,
        )
        db.add(user)
        await db.flush()
        logger.info("Created new user: %s", user.id)
    else:
        if union_id and not user.union_id:
            user.union_id = union_id
        await db.flush()

    token = create_access_token(str(user.id))

    return WxLoginResponse(
        token=token,
        user=UserResponse.model_validate(user),
        is_new_user=is_new_user,
    )
