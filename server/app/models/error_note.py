"""ErrorNote model."""

import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ErrorNote(Base):
    """A wrong-answer entry captured by the student."""

    __tablename__ = "error_notes"
    __table_args__ = (
        Index("ix_error_notes_student_subject", "student_id", "subject_id"),
        Index(
            "ix_error_notes_student_created",
            "student_id",
            "created_at",
            postgresql_using="btree",
        ),
        Index(
            "ix_error_notes_student_knowledge",
            "student_id",
            "knowledge_node_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False
    )
    subject_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("subjects.id"), nullable=False
    )
    knowledge_node_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("knowledge_nodes.id"), nullable=True
    )
    error_type: Mapped[str | None] = mapped_column(
        String(20),
        comment="careless | concept_unclear | method_unknown | other",
    )
    source: Mapped[str | None] = mapped_column(
        String(20),
        comment="monthly | weekly | homework | mock | other",
    )
    question_image_url: Mapped[str] = mapped_column(
        String(512), nullable=False
    )
    correction_image_url: Mapped[str | None] = mapped_column(String(512))
    note: Mapped[str | None] = mapped_column(String(200))
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
