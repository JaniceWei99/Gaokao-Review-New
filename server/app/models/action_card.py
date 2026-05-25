"""ActionCard model."""

import datetime
import uuid

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ActionCard(Base):
    """Pre-defined action card tied to a milestone category + timing."""

    __tablename__ = "action_cards"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    milestone_category: Mapped[str | None] = mapped_column(
        String(30),
        comment=(
            "qualification_exam | level_exam | spring_exam | autumn_exam | "
            "mock_exam | school_exam | registration | volunteer_fill | "
            "result_release | comprehensive_eval | custom"
        ),
    )
    timing: Mapped[str | None] = mapped_column(
        String(15), comment="15d_before | 3d_before"
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    action_items: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="Array of action item objects"
    )
    footer_tip: Mapped[str | None] = mapped_column(String(500))
    applicable_grades: Mapped[dict | None] = mapped_column(JSONB)
    applicable_subjects: Mapped[dict | None] = mapped_column(JSONB)
    quote_category: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
