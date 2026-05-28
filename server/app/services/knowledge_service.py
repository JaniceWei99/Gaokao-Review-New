"""Knowledge tree service — browse and search knowledge nodes."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.knowledge import KnowledgeNode
from app.models.student import Student
from app.middleware.error_handler import ResourceNotFound


async def get_knowledge_tree(
    subject_id: str,
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    max_level: int = 2,
) -> list[dict]:
    """Get the knowledge tree for a subject, up to max_level depth.

    Returns a nested list structure suitable for tree rendering.
    """
    student = await db.get(Student, student_id)
    if student is None or student.user_id != user_id:
        raise ResourceNotFound()

    result = await db.execute(
        select(KnowledgeNode)
        .where(
            KnowledgeNode.subject_id == subject_id,
            KnowledgeNode.is_active == True,
            KnowledgeNode.level <= max_level,
        )
        .order_by(KnowledgeNode.display_order)
    )
    nodes = result.scalars().all()

    node_map = {}
    roots = []
    for node in nodes:
        item = {
            "id": str(node.id),
            "name": node.name,
            "level": node.level,
            "subject_id": node.subject_id,
            "display_order": node.display_order,
            "children": [],
        }
        node_map[str(node.id)] = item
        if node.parent_id is None:
            roots.append(item)
        else:
            parent_key = str(node.parent_id)
            if parent_key in node_map:
                node_map[parent_key]["children"].append(item)

    return roots


async def get_level3_nodes(
    parent_id: uuid.UUID,
    db: AsyncSession,
) -> list[dict]:
    """Get level-3 knowledge nodes for a given level-2 parent (lazy loading)."""
    result = await db.execute(
        select(KnowledgeNode)
        .where(
            KnowledgeNode.parent_id == parent_id,
            KnowledgeNode.is_active == True,
            KnowledgeNode.level == 3,
        )
        .order_by(KnowledgeNode.display_order)
    )
    nodes = result.scalars().all()

    return [
        {
            "id": str(n.id),
            "name": n.name,
            "level": n.level,
            "subject_id": n.subject_id,
            "display_order": n.display_order,
        }
        for n in nodes
    ]
