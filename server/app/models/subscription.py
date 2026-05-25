"""UserSubscription model."""

import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserSubscription(Base):
    """Subscription / billing plan for a user."""

    __tablename__ = "user_subscriptions"
    __table_args__ = (
        Index("ix_user_subscriptions_user_plan", "user_id", "plan"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    plan: Mapped[str | None] = mapped_column(
        String(10), comment="free | standard | premium"
    )
    billing_type: Mapped[str | None] = mapped_column(
        String(25), comment="monthly | yearly | lifetime_high_school"
    )
    price_paid: Mapped[float | None] = mapped_column(Numeric(7, 2))
    started_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_expires_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime
    )
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ──────────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="subscriptions"
    )
