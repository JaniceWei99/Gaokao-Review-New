"""JWT authentication middleware for FastAPI."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.error_handler import Unauthorized

security = HTTPBearer(auto_error=False)


def create_access_token(user_id: str) -> str:
    """Create a JWT access token for the given user ID."""
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expires_hours)
    payload = {
        "sub": str(user_id),
        "exp": expires,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Raises Unauthorized on failure."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise Unauthorized()
        return payload
    except JWTError:
        raise Unauthorized()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> uuid.UUID:
    """FastAPI dependency: extract and validate user ID from JWT token."""
    if credentials is None:
        raise Unauthorized()
    payload = decode_access_token(credentials.credentials)
    try:
        return uuid.UUID(payload["sub"])
    except (ValueError, KeyError):
        raise Unauthorized()


async def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """FastAPI dependency: get the full User object for the authenticated user."""
    from app.models.user import User

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if user is None:
        raise Unauthorized()
    return user
