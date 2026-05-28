"""Knowledge tree router — browse knowledge nodes by subject."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.services.knowledge_service import get_knowledge_tree, get_level3_nodes

router = APIRouter()


@router.get("")
async def browse_knowledge_tree(
    subject_id: str = Query(..., description="Subject ID, e.g. 'math'"),
    student_id: uuid.UUID = Query(...),
    max_level: int = Query(2, ge=1, le=3, description="Max depth to return"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Browse the knowledge tree for a subject (default 2 levels)."""
    return await get_knowledge_tree(subject_id, student_id, user_id, db, max_level)


@router.get("/level3/{parent_id}")
async def get_level3(
    parent_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Lazy-load level-3 nodes for a given level-2 parent."""
    return await get_level3_nodes(parent_id, db)
