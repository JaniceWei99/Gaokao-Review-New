"""GrowthRecord model."""

import datetime
import uuid

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GrowthRecord(Base):
    """Student growth / achievement record."""

    __tablename__ = "growth_records"
    __table_args__ = (
        Index(
            "ix_growth_records_student_date",
            "student_id",
            "record_date",
            postgresql_using="btree",
        ),
        Index(
            "ix_growth_records_student_type",
            "student_id",
            "record_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False
    )
    record_type: Mapped[str | None] = mapped_column(
        String(20),
        comment="award | progress | performance | breakthrough | memo",
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    record_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    category: Mapped[str | None] = mapped_column(
        String(30),
        comment=(
            "academic_competition | sports | comprehensive | "
            "social_practice | other"
        ),
    )
    awarding_body: Mapped[str | None] = mapped_column(String(100))
    image_url: Mapped[str | None] = mapped_column(String(512))
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    linked_quote_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("daily_quotes.id"), nullable=True
    )
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
    linked_quote: Mapped["DailyQuote | None"] = relationship()  # noqa: F821
