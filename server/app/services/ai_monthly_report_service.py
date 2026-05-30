"""AI monthly report service — generate monthly growth reports with AI analysis."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_note import ErrorNote
from app.models.exam import Exam
from app.models.growth_record import GrowthRecord
from app.models.milestone import Milestone
from app.models.student import Student
from app.services.compliance_filter import build_system_prompt
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)

MONTHLY_REPORT_SYSTEM_PROMPT = """你是"高考家长帮"的月度报告生成器，为上海高考生家长生成月度成长报告。

你的任务：
- 根据本月的数据（成绩变化、错题趋势、成长亮点、里程碑完成情况），生成一份温暖的月度总结
- 报告要突出进步和亮点，对不足之处用建设性的语言表达
- 语气温暖、鼓励、积极，不制造焦虑

输出格式（JSON）：
{
  "title": "XX月成长报告",
  "summary": "一段话总结本月整体表现（100-200字）",
  "highlights": [
    {"title": "亮点标题", "description": "亮点描述"}
  ],
  "score_analysis": "成绩变化分析（100-150字）",
  "error_analysis": "错题趋势分析（100-150字，不涉及具体题目解答）",
  "growth_moments": "成长闪光时刻（100-150字）",
  "next_month_suggestions": [
    {"title": "建议标题", "description": "具体建议"}
  ],
  "encouragement": "给家长的一段鼓励（50-100字）"
}

严格合规要求：
- 不讲解学科知识
- 不解答题目
- 只做数据总结和家长层面的建议
"""


async def generate_monthly_report(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    year: int,
    month: int,
    db: AsyncSession,
) -> dict:
    """Generate an AI-powered monthly growth report."""
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        from app.middleware.error_handler import StudentNotFound
        raise StudentNotFound()

    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    exam_data = await _get_exam_data(student_id, start_date, end_date, db)
    error_data = await _get_error_data(student_id, start_date, end_date, db)
    growth_data = await _get_growth_data(student_id, start_date, end_date, db)
    milestone_data = await _get_milestone_data(student_id, start_date, end_date, db)

    student_name = student.nickname or "孩子"

    context = f"""
学生：{student_name}
年级：{student.grade or '未知'}
选考科目：{student.elective_subjects or '未选择'}
报告月份：{year}年{month}月

本月成绩记录：
{exam_data}

本月错题情况：
{error_data}

本月成长记录：
{growth_data}

本月里程碑：
{milestone_data}
"""

    system_prompt = build_system_prompt(MONTHLY_REPORT_SYSTEM_PROMPT)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请根据以下数据生成月度成长报告：\n{context}"},
    ]

    try:
        response = await llm_client.chat(messages, json_mode=True, max_tokens=2048)
        import json

        content = response["content"]
        report = json.loads(content)
        report["year"] = year
        report["month"] = month
        report["student_name"] = student_name
        return report
    except Exception as exc:
        logger.error("Failed to generate monthly report: %s", exc)
        return {
            "title": f"{month}月成长报告",
            "summary": f"{student_name}本月的数据已记录，AI报告生成失败，请稍后再试。",
            "highlights": [],
            "score_analysis": "",
            "error_analysis": "",
            "growth_moments": "",
            "next_month_suggestions": [],
            "encouragement": "每一步都在进步，继续加油！",
            "year": year,
            "month": month,
            "student_name": student_name,
        }


async def _get_exam_data(
    student_id: uuid.UUID, start_date: date, end_date: date, db: AsyncSession
) -> str:
    result = await db.execute(
        select(Exam)
        .where(
            Exam.student_id == student_id,
            Exam.exam_date >= start_date,
            Exam.exam_date < end_date,
        )
        .order_by(Exam.exam_date)
    )
    exams = result.scalars().all()

    if not exams:
        return "本月无成绩记录"

    lines = []
    for exam in exams:
        scores = exam.scores or []
        score_str = ", ".join(
            f"{s.get('subject_id', '?')}: {s.get('score', '?')}/{s.get('max_score', '?')}"
            for s in scores
        )
        lines.append(f"- {exam.exam_date} {exam.title or '考试'}: {score_str}")

    return "\n".join(lines)


async def _get_error_data(
    student_id: uuid.UUID, start_date: date, end_date: date, db: AsyncSession
) -> str:
    result = await db.execute(
        select(ErrorNote.subject_id, func.count(ErrorNote.id))
        .where(
            ErrorNote.student_id == student_id,
            ErrorNote.created_at >= datetime(start_date.year, start_date.month, start_date.day),
            ErrorNote.created_at < datetime(end_date.year, end_date.month, end_date.day),
        )
        .group_by(ErrorNote.subject_id)
        .order_by(func.count(ErrorNote.id).desc())
    )
    counts = result.all()

    if not counts:
        return "本月无新增错题"

    total = sum(c for _, c in counts)
    lines = [f"本月新增{total}道错题"]
    for subject_id, count in counts:
        lines.append(f"- {subject_id}: {count}道")

    return "\n".join(lines)


async def _get_growth_data(
    student_id: uuid.UUID, start_date: date, end_date: date, db: AsyncSession
) -> str:
    result = await db.execute(
        select(GrowthRecord)
        .where(
            GrowthRecord.student_id == student_id,
            GrowthRecord.event_date >= start_date,
            GrowthRecord.event_date < end_date,
        )
        .order_by(GrowthRecord.event_date)
    )
    records = result.scalars().all()

    if not records:
        return "本月无成长记录"

    lines = []
    for r in records:
        lines.append(f"- {r.event_date}: {r.title or r.description[:50] if r.description else '记录'}")

    return "\n".join(lines)


async def _get_milestone_data(
    student_id: uuid.UUID, start_date: date, end_date: date, db: AsyncSession
) -> str:
    result = await db.execute(
        select(Milestone)
        .where(
            Milestone.student_id == student_id,
            Milestone.event_date >= start_date,
            Milestone.event_date < end_date,
        )
        .order_by(Milestone.event_date)
    )
    milestones = result.scalars().all()

    if not milestones:
        return "本月无里程碑事件"

    lines = []
    for m in milestones:
        lines.append(f"- {m.event_date}: {m.title}")

    return "\n".join(lines)
