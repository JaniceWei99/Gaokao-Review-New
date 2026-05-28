"""AI error note classification service — classify error notes to knowledge points without giving answers."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_note import ErrorNote
from app.models.knowledge import KnowledgeNode
from app.models.student import Student
from app.services.compliance_filter import build_system_prompt
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)

CLASSIFICATION_SYSTEM_PROMPT = """你是"高考复习助手"的错题分类助手，帮助家长将孩子的错题归类到对应的知识点。

你的任务：
- 根据错题的描述、科目信息，判断这道题属于哪个知识模块/章节
- 只做分类，绝对不给答案、不讲解解题方法
- 如果有图片描述，根据描述进行分类

输出格式（JSON）：
{
  "subject_id": "科目ID（如math/physics/chemistry等）",
  "suggested_chapter": "建议归入的章节名称",
  "suggested_knowledge_points": ["知识点1", "知识点2"],
  "difficulty_assessment": "基础/中等/较难",
  "study_advice": "给家长的建议（如何帮助孩子攻克这类题目，不涉及具体解法）"
}

严格合规要求：
- 绝对不给出题目答案
- 绝对不讲解解题步骤
- 只做知识点分类和学习策略建议
- 如果无法确定分类，给出最可能的方向
"""


async def classify_error_note(
    error_note_id: uuid.UUID,
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Classify an error note to knowledge points using AI."""
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        from app.middleware.error_handler import StudentNotFound
        raise StudentNotFound()

    note_result = await db.execute(
        select(ErrorNote).where(
            ErrorNote.id == error_note_id,
            ErrorNote.student_id == student_id,
        )
    )
    note = note_result.scalar_one_or_none()
    if not note:
        from app.middleware.error_handler import ResourceNotFound
        raise ResourceNotFound()

    context = _build_classification_context(note, student)

    system_prompt = build_system_prompt(CLASSIFICATION_SYSTEM_PROMPT)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请对以下错题进行分类：\n{context}"},
    ]

    try:
        response = await llm_client.chat(messages, json_mode=True)
        import json

        content = response["content"]
        classification = json.loads(content)

        if note.subject_id and not classification.get("subject_id"):
            classification["subject_id"] = note.subject_id

        return classification
    except Exception as exc:
        logger.error("Failed to classify error note: %s", exc)
        return {
            "subject_id": note.subject_id or "unknown",
            "suggested_chapter": "分类失败，请手动选择",
            "suggested_knowledge_points": [],
            "difficulty_assessment": "未知",
            "study_advice": "AI分类暂时不可用，建议根据科目和章节手动归类。",
        }


async def batch_classify_error_notes(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    subject_id: str | None,
    db: AsyncSession,
) -> dict:
    """Get a summary of error note classification for a subject."""
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        from app.middleware.error_handler import StudentNotFound
        raise StudentNotFound()

    query = select(ErrorNote).where(ErrorNote.student_id == student_id)
    if subject_id:
        query = query.where(ErrorNote.subject_id == subject_id)
    query = query.order_by(ErrorNote.created_at.desc()).limit(50)

    note_result = await db.execute(query)
    notes = note_result.scalars().all()

    if not notes:
        return {
            "total": 0,
            "by_subject": {},
            "weak_areas": [],
            "summary": "暂无错题记录",
        }

    by_subject: dict[str, int] = {}
    for note in notes:
        sid = note.subject_id or "unknown"
        by_subject[sid] = by_subject.get(sid, 0) + 1

    context_parts = []
    for note in notes[:20]:
        desc = note.description or note.title or "无描述"
        context_parts.append(f"- [{note.subject_id or '?'}] {desc[:100]}")

    context = "\n".join(context_parts)

    summary_prompt = build_system_prompt(
        """你是错题分析助手。根据错题列表，分析薄弱环节。
只给出知识点层面的分析，不涉及具体题目解答。
输出JSON：{"weak_areas": [{"subject": "科目", "area": "薄弱知识点", "count": 数量}], "summary": "一句话总结"}"""
    )

    messages = [
        {"role": "system", "content": summary_prompt},
        {"role": "user", "content": f"分析以下错题的薄弱环节：\n{context}"},
    ]

    try:
        response = await llm_client.chat(messages, json_mode=True, max_tokens=512)
        import json

        analysis = json.loads(response["content"])
        return {
            "total": len(notes),
            "by_subject": by_subject,
            "weak_areas": analysis.get("weak_areas", []),
            "summary": analysis.get("summary", ""),
        }
    except Exception as exc:
        logger.error("Failed to batch classify: %s", exc)
        return {
            "total": len(notes),
            "by_subject": by_subject,
            "weak_areas": [],
            "summary": f"共{len(notes)}道错题，AI分析暂时不可用",
        }


def _build_classification_context(note: ErrorNote, student: Student) -> str:
    parts = [
        f"科目：{note.subject_id or '未知'}",
        f"年级：{student.grade or '未知'}",
        f"选考科目：{student.elective_subjects or '未选择'}",
    ]

    if note.title:
        parts.append(f"错题标题：{note.title}")
    if note.description:
        parts.append(f"错题描述：{note.description[:500]}")
    if note.my_answer:
        parts.append(f"学生的作答：{note.my_answer[:200]}")
    if note.tags:
        parts.append(f"标签：{', '.join(note.tags) if isinstance(note.tags, list) else str(note.tags)}")

    if note.image_urls:
        parts.append(f"图片数量：{len(note.image_urls)}张（图片仅供参考分类，不用于解题）")

    return "\n".join(parts)
