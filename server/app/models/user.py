"""User model."""

import datetime
import uuid

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """WeChat user account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    openid: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, comment="WeChat openid"
    )
    union_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    nickname: Mapped[str | None] = mapped_column(String(64))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Relationships ──────────────────────────────────────────
    students: Mapped[list["Student"]] = relationship(  # noqa: F821
        back_populates="user", lazy="selectin"
    )
    quote_favorites: Mapped[list["UserQuoteFavorite"]] = relationship(  # noqa: F821
        back_populates="user", lazy="selectin"
    )
    subscriptions: Mapped[list["UserSubscription"]] = relationship(  # noqa: F821
        back_populates="user", lazy="selectin"
    )
