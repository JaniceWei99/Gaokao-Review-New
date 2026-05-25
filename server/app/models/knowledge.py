"""KnowledgeNode model (three-level tree)."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class KnowledgeNode(Base):
    """Three-level knowledge tree node."""

    __tablename__ = "knowledge_nodes"
    __table_args__ = (
        Index("ix_knowledge_nodes_subject_level", "subject_id", "level"),
        Index("ix_knowledge_nodes_parent", "parent_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    subject_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("subjects.id"), nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("knowledge_nodes.id"), nullable=True
    )
    level: Mapped[int] = mapped_column(
        Integer, comment="1, 2, or 3"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Relationships ──────────────────────────────────────────
    subject: Mapped["Subject"] = relationship(  # noqa: F821
        back_populates="knowledge_nodes"
    )
    parent: Mapped["KnowledgeNode | None"] = relationship(
        back_populates="children", remote_side=[id]
    )
    children: Mapped[list["KnowledgeNode"]] = relationship(
        back_populates="parent", lazy="selectin"
    )
