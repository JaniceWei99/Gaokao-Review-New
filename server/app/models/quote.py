"""DailyQuote, UserQuoteFavorite, and UserQuoteHistory models."""

import datetime
import uuid

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DailyQuote(Base):
    """Inspirational quote shown to students."""

    __tablename__ = "daily_quotes"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    content: Mapped[str] = mapped_column(String(100), nullable=False)
    author: Mapped[str | None] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(
        String(30),
        comment=(
            "daily_encouragement | study_method | pre_exam_motivation | "
            "stress_relief | post_exam_relief | parent_child_warmth | "
            "famous_quotes | gao1_special"
        ),
    )
    applicable_grades: Mapped[dict | None] = mapped_column(JSONB)
    applicable_phase: Mapped[str | None] = mapped_column(
        String(20),
        comment="normal | pre_exam_30d | pre_exam_7d | post_exam | all",
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class UserQuoteFavorite(Base):
    """User's favorited quotes."""

    __tablename__ = "user_quote_favorites"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "quote_id",
            name="uq_user_quote_favorite",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    quote_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_quotes.id"), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="quote_favorites"
    )
    quote: Mapped["DailyQuote"] = relationship()


class UserQuoteHistory(Base):
    """Which quote was shown to a student on a given date."""

    __tablename__ = "user_quote_history"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "display_date",
            name="uq_user_quote_history_student_date",
        ),
        Index("ix_user_quote_history_student_date", "student_id", "display_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False
    )
    quote_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_quotes.id"), nullable=False
    )
    display_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    # ── Relationships ──────────────────────────────────────────
    student: Mapped["Student"] = relationship(  # noqa: F821
        foreign_keys=[student_id]
    )
    quote: Mapped["DailyQuote"] = relationship()
