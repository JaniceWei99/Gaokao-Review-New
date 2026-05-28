"""AI chat router — AI parent advisor conversation endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.middleware.permission import require_premium
from app.schemas.ai_chat import (
    ChatListResponse,
    ChatRequest,
    ChatSessionResponse,
    ChatSessionSummary,
)
from app.services.ai_chat_service import (
    delete_session,
    get_session_messages,
    list_sessions,
    send_chat_message,
)

router = APIRouter()


@router.post("")
async def send_message(
    student_id: uuid.UUID,
    body: ChatRequest,
    plan: str = Depends(require_premium),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to the AI parent advisor. Requires premium plan."""
    return await send_chat_message(user_id, student_id, body.message, body.session_id, db)


@router.get("/sessions", response_model=ChatListResponse)
async def get_sessions(
    student_id: uuid.UUID,
    plan: str = Depends(require_premium),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions for a student. Requires premium plan."""
    sessions = await list_sessions(user_id, student_id, db)
    return ChatListResponse(
        sessions=[ChatSessionSummary(**s) for s in sessions],
        total=len(sessions),
    )


@router.get("/sessions/{session_id}")
async def get_messages(
    student_id: uuid.UUID,
    session_id: uuid.UUID,
    plan: str = Depends(require_premium),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a chat session. Requires premium plan."""
    messages = await get_session_messages(user_id, session_id, db)
    return {"messages": messages}


@router.delete("/sessions/{session_id}", status_code=204)
async def remove_session(
    student_id: uuid.UUID,
    session_id: uuid.UUID,
    plan: str = Depends(require_premium),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session. Requires premium plan."""
    await delete_session(user_id, session_id, db)
