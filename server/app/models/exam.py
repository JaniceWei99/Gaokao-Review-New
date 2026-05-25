"""Exam and ExamScore models."""

import datetime
import uuid

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Exam(Base):
    """An exam instance for a student."""

    __tablename__ = "exams"
    __table_args__ = (
        Index("ix_exams_student_date", "student_id", "exam_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    exam_type: Mapped[str | None] = mapped_column(
        String(20),
        comment="monthly | midterm | final | mock1 | mock2 | mock3 | other",
    )
    exam_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ──────────────────────────────────────────
    student: Mapped["Student"] = relationship(  # noqa: F821
        foreign_keys=[student_id]
    )
    scores: Mapped[list["ExamScore"]] = relationship(
        back_populates="exam", lazy="selectin", cascade="all, delete-orphan"
    )


class ExamScore(Base):
    """Individual subject score within an exam."""

    __tablename__ = "exam_scores"
    __table_args__ = (
        UniqueConstraint(
            "exam_id", "subject_id",
            name="uq_exam_score_exam_subject",
        ),
        Index("ix_exam_scores_exam", "exam_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("subjects.id"), nullable=False
    )
    score: Mapped[float] = mapped_column(Numeric(5, 1), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(5, 1), nullable=False)
    score_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 2), comment="score / max_score * 100"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────────
    exam: Mapped["Exam"] = relationship(back_populates="scores")
    subject: Mapped["Subject"] = relationship()  # noqa: F821
