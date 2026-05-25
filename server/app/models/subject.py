"""Subject model."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Subject(Base):
    """System-preset subject (e.g. chinese, math, english)."""

    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(
        String(20), primary_key=True, comment="e.g. 'chinese', 'math'"
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str | None] = mapped_column(
        String(10), comment="required | elective"
    )
    gaokao_max_score: Mapped[int] = mapped_column(Integer, nullable=False)
    display_order: Mapped[int | None] = mapped_column(Integer)
    icon: Mapped[str | None] = mapped_column(String(50))

    # ── Relationships ──────────────────────────────────────────
    knowledge_nodes: Mapped[list["KnowledgeNode"]] = relationship(  # noqa: F821
        back_populates="subject", lazy="selectin"
    )
