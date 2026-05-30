"""Student model."""

import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Student(Base):
    """Student profile linked to a user account."""

    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    grade: Mapped[str | None] = mapped_column(
        String(4), comment="gao1 | gao2 | gao3"
    )
    province: Mapped[str | None] = mapped_column(
        String(30), default="shanghai", comment="省份ID (e.g. shanghai, beijing)"
    )
    region_code: Mapped[str | None] = mapped_column(
        String(20), comment="地区/区县编码"
    )
    has_selected_subjects: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    selected_subject_1: Mapped[str | None] = mapped_column(String(20))
    selected_subject_2: Mapped[str | None] = mapped_column(String(20))
    selected_subject_3: Mapped[str | None] = mapped_column(String(20))
    has_jan_english_exam: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ──────────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="students"
    )
