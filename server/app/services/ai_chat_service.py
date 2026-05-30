"""AI chat service — handles conversation logic, context management, and LLM calls."""

from __future__ import annotations

import datetime
import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.middleware.error_handler import AppException, RateLimitExceeded
from app.models.ai_chat import AIChatMessage, AIChatSession
from app.models.student import Student
from app.services.ai_cost_control import (
    check_daily_chat_limit,
    get_cached_similar_response,
    increment_chat_count,
    cache_similar_response,
    simple_hash,
    track_token_usage,
)
from app.services.compliance_filter import (
    build_system_prompt,
    check_input_compliance,
    check_output_compliance,
)
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)

ADVISOR_SYSTEM_PROMPT = """你是"高考家长帮"的AI家长顾问，专门帮助上海高考生的家长。

你的角色：
- 陪伴家长度过孩子备考阶段，提供情感支持和实用建议
- 根据孩子的选科、年级、当前阶段给出个性化建议
- 帮助家长理解孩子的学习节奏，避免过度焦虑
- 提供时间管理、心理调适方面的指导

你的语气：
- 温暖、理解、鼓励
- 不制造焦虑，不贩卖焦虑
- 尊重每个孩子的节奏和特点
- 用通俗易懂的语言，避免教育术语

你可以谈论：
- 家长如何陪伴孩子备考
- 如何帮助孩子管理时间和压力
- 如何与孩子沟通学习问题
- 如何关注孩子的身心健康
- 如何在不同阶段调整陪伴策略
- 如何看待成绩波动
- 如何营造良好的家庭学习氛围

你绝对不能：
- 讲解任何学科知识
- 解答任何题目
- 给出考试答案或解题步骤
- 分析具体题目的解法
"""


async def get_or_create_session(
    user_id: uuid.UUID,
    student_id: uuid.UUID,
    session_id: uuid.UUID | None,
    db: AsyncSession,
) -> AIChatSession:
    """Get existing session or create a new one."""
    if session_id:
        result = await db.execute(
            select(AIChatSession).where(
                AIChatSession.id == session_id,
                AIChatSession.user_id == user_id,
            )
        )
        session = result.scalar_one_or_none()
        if session:
            return session

    today = datetime.date.today()
    result = await db.execute(
        select(AIChatSession)
        .where(
            AIChatSession.user_id == user_id,
            AIChatSession.student_id == student_id,
            AIChatSession.created_date == today,
        )
        .order_by(AIChatSession.created_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if session:
        return session

    session = AIChatSession(
        user_id=user_id,
        student_id=student_id,
        created_date=today,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def build_context_messages(
    session: AIChatSession,
    student: Student,
    user_message: str,
    db: AsyncSession,
) -> list[dict[str, str]]:
    """Build the message list for LLM call with context."""
    student_context = f"""
学生信息：
- 年级：{student.grade or '未知'}
- 选考科目：{student.elective_subjects or '未选择'}
- 英语考试类型：{student.english_exam_type or '未知'}
"""

    system_prompt = build_system_prompt(ADVISOR_SYSTEM_PROMPT + student_context)

    messages = [{"role": "system", "content": system_prompt}]

    result = await db.execute(
        select(AIChatMessage)
        .where(AIChatMessage.session_id == session.id)
        .order_by(AIChatMessage.created_at.desc())
        .limit(settings.ai_max_context_rounds * 2)
    )
    history = list(reversed(result.scalars().all()))

    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_message})

    return messages


async def send_chat_message(
    user_id: uuid.UUID,
    student_id: uuid.UUID,
    message: str,
    session_id: uuid.UUID | None,
    db: AsyncSession,
) -> dict:
    """Process a chat message and return AI response."""
    is_within_limit, current_count = await check_daily_chat_limit(
        str(user_id), settings.ai_daily_chat_limit
    )
    if not is_within_limit:
        raise RateLimitExceeded()

    is_compliant, reason = check_input_compliance(message)
    if not is_compliant:
        return {
            "content": reason,
            "is_compliant": False,
            "remaining_chats": settings.ai_daily_chat_limit - current_count,
        }

    question_hash = simple_hash(message)
    cached_response = await get_cached_similar_response(question_hash)
    if cached_response:
        session = await get_or_create_session(user_id, student_id, session_id, db)
        user_msg = AIChatMessage(
            session_id=session.id, role="user", content=message
        )
        db.add(user_msg)
        assistant_msg = AIChatMessage(
            session_id=session.id, role="assistant", content=cached_response
        )
        db.add(assistant_msg)
        await db.commit()

        await increment_chat_count(str(user_id))
        remaining = settings.ai_daily_chat_limit - current_count - 1

        return {
            "session_id": str(session.id),
            "content": cached_response,
            "is_compliant": True,
            "remaining_chats": max(0, remaining),
        }

    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        from app.middleware.error_handler import StudentNotFound
        raise StudentNotFound()

    session = await get_or_create_session(user_id, student_id, session_id, db)

    context_messages = await build_context_messages(session, student, message, db)

    user_msg = AIChatMessage(
        session_id=session.id, role="user", content=message
    )
    db.add(user_msg)
    await db.commit()

    try:
        llm_response = await llm_client.chat(context_messages)
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        raise AppException("INTERNAL_ERROR", "AI服务暂时不可用，请稍后再试", 500)

    ai_content = llm_response["content"]
    usage = llm_response.get("usage", {})

    is_output_compliant, sanitized = check_output_compliance(ai_content)
    if not is_output_compliant:
        ai_content = sanitized

    if not session.title:
        session.title = message[:50]

    assistant_msg = AIChatMessage(
        session_id=session.id,
        role="assistant",
        content=ai_content,
        token_count=usage.get("total_tokens"),
    )
    db.add(assistant_msg)
    await db.commit()

    await increment_chat_count(str(user_id))

    if usage.get("prompt_tokens") and usage.get("completion_tokens"):
        await track_token_usage(
            str(user_id),
            usage["prompt_tokens"],
            usage["completion_tokens"],
        )

    if is_output_compliant:
        await cache_similar_response(question_hash, ai_content)

    remaining = settings.ai_daily_chat_limit - current_count - 1

    return {
        "session_id": str(session.id),
        "content": ai_content,
        "is_compliant": is_output_compliant,
        "remaining_chats": max(0, remaining),
    }


async def list_sessions(
    user_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession,
) -> list[dict]:
    """List chat sessions for a student."""
    result = await db.execute(
        select(AIChatSession)
        .where(
            AIChatSession.user_id == user_id,
            AIChatSession.student_id == student_id,
        )
        .order_by(AIChatSession.created_at.desc())
        .limit(20)
    )
    sessions = result.scalars().all()

    out = []
    for s in sessions:
        msg_result = await db.execute(
            select(AIChatMessage)
            .where(AIChatMessage.session_id == s.id)
            .order_by(AIChatMessage.created_at.desc())
            .limit(1)
        )
        last_msg = msg_result.scalar_one_or_none()

        count_result = await db.execute(
            select(func.count())
            .select_from(AIChatMessage)
            .where(AIChatMessage.session_id == s.id)
        )
        msg_count = count_result.scalar() or 0

        out.append({
            "id": str(s.id),
            "title": s.title,
            "created_date": s.created_date.isoformat(),
            "last_message": last_msg.content[:100] if last_msg else None,
            "message_count": msg_count,
        })

    return out


async def get_session_messages(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession,
) -> list[dict]:
    """Get all messages in a session."""
    result = await db.execute(
        select(AIChatSession).where(
            AIChatSession.id == session_id,
            AIChatSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        from app.middleware.error_handler import ResourceNotFound
        raise ResourceNotFound()

    msg_result = await db.execute(
        select(AIChatMessage)
        .where(AIChatMessage.session_id == session_id)
        .order_by(AIChatMessage.created_at)
    )
    messages = msg_result.scalars().all()

    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


async def delete_session(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Delete a chat session and all its messages."""
    result = await db.execute(
        select(AIChatSession).where(
            AIChatSession.id == session_id,
            AIChatSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        from app.middleware.error_handler import ResourceNotFound
        raise ResourceNotFound()

    await db.delete(session)
    await db.commit()
