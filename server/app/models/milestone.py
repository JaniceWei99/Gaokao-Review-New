"""Milestone and MilestoneReminder models."""

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


class Milestone(Base):
    """System or custom milestone event."""

    __tablename__ = "milestones"
    __table_args__ = (
        Index("ix_milestones_event_date", "event_date"),
        Index("ix_milestones_category", "category"),
        Index("ix_milestones_student", "student_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    type: Mapped[str | None] = mapped_column(
        String(10), comment="system | custom"
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("students.id"),
        nullable=True,
        comment="NULL for system milestones",
    )
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))
    event_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    event_end_date: Mapped[datetime.date | None] = mapped_column(Date)
    category: Mapped[str | None] = mapped_column(
        String(30),
        comment=(
            "qualification_exam | level_exam | spring_exam | autumn_exam | "
            "mock_exam | school_exam | registration | volunteer_fill | "
            "result_release | comprehensive_eval | custom"
        ),
    )
    applicable_grades: Mapped[dict | None] = mapped_column(
        JSONB, comment='e.g. ["gao3"]'
    )
    applicable_subjects: Mapped[dict | None] = mapped_column(JSONB)
    applicable_districts: Mapped[dict | None] = mapped_column(JSONB)
    requires_jan_english: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    remind_15d: Mapped[bool] = mapped_column(Boolean, default=True)
    remind_3d: Mapped[bool] = mapped_column(Boolean, default=True)
    action_card_15d_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("action_cards.id"), nullable=True
    )
    action_card_3d_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("action_cards.id"), nullable=True
    )
    is_dynamic_date: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ──────────────────────────────────────────
    student: Mapped["Student | None"] = relationship(  # noqa: F821
        foreign_keys=[student_id]
    )
    action_card_15d: Mapped["ActionCard | None"] = relationship(  # noqa: F821
        foreign_keys=[action_card_15d_id]
    )
    action_card_3d: Mapped["ActionCard | None"] = relationship(  # noqa: F821
        foreign_keys=[action_card_3d_id]
    )
    reminders: Mapped[list["MilestoneReminder"]] = relationship(
        back_populates="milestone", lazy="selectin"
    )


class MilestoneReminder(Base):
    """Tracks whether a reminder was sent / opened for a milestone."""

    __tablename__ = "milestone_reminders"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "milestone_id", "timing",
            name="uq_milestone_reminder_student_milestone_timing",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False
    )
    milestone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("milestones.id"), nullable=False
    )
    timing: Mapped[str | None] = mapped_column(
        String(15), comment="15d_before | 3d_before"
    )
    sent_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    opened: Mapped[bool] = mapped_column(Boolean, default=False)
    opened_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    action_items_checked: Mapped[dict | None] = mapped_column(
        JSONB, server_default="[]"
    )

    # ── Relationships ──────────────────────────────────────────
    student: Mapped["Student"] = relationship(  # noqa: F821
        foreign_keys=[student_id]
    )
    milestone: Mapped["Milestone"] = relationship(
        back_populates="reminders"
    )
