"""SchoolProgress model."""

import datetime
import uuid

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SchoolProgress(Base):
    """Tracks what the school is currently teaching for a subject."""

    __tablename__ = "school_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False
    )
    subject_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("subjects.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[datetime.date | None] = mapped_column(Date)
    end_date: Mapped[datetime.date | None] = mapped_column(Date)
    knowledge_node_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("knowledge_nodes.id"), nullable=True
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
    subject: Mapped["Subject"] = relationship()  # noqa: F821
    knowledge_node: Mapped["KnowledgeNode | None"] = relationship()  # noqa: F821
