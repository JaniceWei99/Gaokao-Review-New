"""AI action suggestion service — generate personalized action suggestions based on student data."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_note import ErrorNote
from app.models.exam import Exam
from app.models.milestone import Milestone
from app.models.student import Student
from app.services.compliance_filter import build_system_prompt
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)

ACTION_SUGGESTION_SYSTEM_PROMPT = """你是"高考家长帮"的AI建议生成器，专门为上海高考生家长生成个性化的行动建议。

你的任务：
- 根据学生的选科、年级、当前阶段、错题分布、成绩趋势，生成具体的家长行动建议
- 建议必须具体、可执行，不要空泛的鼓励
- 每条建议包含：标题、详细说明、优先级（高/中/低）
- 生成3-5条建议

输出格式（JSON）：
{
  "suggestions": [
    {
      "title": "建议标题",
      "description": "详细说明，包含具体行动步骤",
      "priority": "high",
      "category": "study_rhythm | emotional_support | time_management | exam_prep | daily_life"
    }
  ],
  "summary": "一句话总结当前阶段最需要关注的重点"
}

分类说明：
- study_rhythm: 学习节奏调整
- emotional_support: 心理情感支持
- time_management: 时间管理建议
- exam_prep: 考前准备建议
- daily_life: 日常生活关怀

严格合规要求：
- 不讲解学科知识
- 不解答题目
- 只提供家长层面的陪伴和指导建议
"""


async def generate_action_suggestions(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Generate personalized action suggestions for a student's parent."""
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        from app.middleware.error_handler import StudentNotFound
        raise StudentNotFound()

    student_context = _build_student_context(student, db)

    exam_summary = await _get_exam_summary(student_id, db)
    error_summary = await _get_error_summary(student_id, db)
    milestone_summary = await _get_milestone_summary(student_id, db)

    context = f"""
学生信息：
- 年级：{student.grade or '未知'}
- 选考科目：{student.elective_subjects or '未选择'}
- 英语考试类型：{student.english_exam_type or '未知'}

成绩概况：
{exam_summary}

错题分布：
{error_summary}

近期里程碑：
{milestone_summary}
"""

    system_prompt = build_system_prompt(ACTION_SUGGESTION_SYSTEM_PROMPT)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请根据以下学生数据，生成个性化行动建议：\n{context}"},
    ]

    try:
        response = await llm_client.chat(messages, json_mode=True)
        import json

        content = response["content"]
        suggestions = json.loads(content)
        return suggestions
    except json.JSONDecodeError:
        logger.warning("AI returned non-JSON response for action suggestions")
        return {
            "suggestions": [],
            "summary": "AI建议生成失败，请稍后再试",
        }
    except Exception as exc:
        logger.error("Failed to generate action suggestions: %s", exc)
        return {
            "suggestions": [],
            "summary": "AI建议生成失败，请稍后再试",
        }


def _build_student_context(student: Student, db: AsyncSession) -> str:
    parts = [
        f"年级：{student.grade or '未知'}",
        f"选考科目：{student.elective_subjects or '未选择'}",
        f"英语考试类型：{student.english_exam_type or '未知'}",
    ]
    return "\n".join(parts)


async def _get_exam_summary(student_id: uuid.UUID, db: AsyncSession) -> str:
    result = await db.execute(
        select(Exam)
        .where(Exam.student_id == student_id)
        .order_by(Exam.exam_date.desc())
        .limit(5)
    )
    exams = result.scalars().all()

    if not exams:
        return "暂无成绩记录"

    lines = []
    for exam in exams:
        scores = exam.scores or []
        score_str = ", ".join(
            f"{s.get('subject_id', '?')}: {s.get('score', '?')}/{s.get('max_score', '?')}"
            for s in scores
        )
        lines.append(f"- {exam.exam_date}: {score_str}")

    return "\n".join(lines)


async def _get_error_summary(student_id: uuid.UUID, db: AsyncSession) -> str:
    result = await db.execute(
        select(ErrorNote.subject_id, func.count(ErrorNote.id))
        .where(ErrorNote.student_id == student_id)
        .group_by(ErrorNote.subject_id)
        .order_by(func.count(ErrorNote.id).desc())
    )
    counts = result.all()

    if not counts:
        return "暂无错题记录"

    lines = []
    for subject_id, count in counts:
        lines.append(f"- {subject_id}: {count}道")

    total = sum(c for _, c in counts)
    return f"共{total}道错题\n" + "\n".join(lines)


async def _get_milestone_summary(student_id: uuid.UUID, db: AsyncSession) -> str:
    from datetime import date

    result = await db.execute(
        select(Milestone)
        .where(
            Milestone.student_id == student_id,
            Milestone.event_date >= date.today(),
        )
        .order_by(Milestone.event_date)
        .limit(5)
    )
    milestones = result.scalars().all()

    if not milestones:
        return "暂无近期里程碑"

    lines = []
    for m in milestones:
        days = (m.event_date - date.today()).days
        lines.append(f"- {m.title} ({m.event_date}, 还有{days}天)")

    return "\n".join(lines)
