"""AI quote generation service — generate personalized daily quotes."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.services.compliance_filter import build_system_prompt
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)

QUOTE_GENERATION_SYSTEM_PROMPT = """你是"高考家长帮"的金句生成器，为高考生家长生成个性化每日金句。

你的任务：
- 根据学生的名字、选科、年级、当前阶段，生成一条温暖有力量的金句
- 金句要融入学生的具体信息，让家长感到这是专门为自己孩子写的
- 语气温暖、鼓励、不焦虑
- 金句长度30-80字

输出格式（JSON）：
{
  "content": "金句内容",
  "author": "AI家长顾问",
  "category": "personalized",
  "context_note": "生成这条金句的背景考虑（开发调试用）"
}

金句风格参考：
- "小明的每一次翻书，都是在为未来铺路。高三的每一分钟都算数。"
- "物理和化学的路上，小红从不孤单。每道错题都是进步的阶梯。"
- "距离春考还有60天，这不是倒计时，而是冲刺的号角。"

严格合规要求：
- 不讲解学科知识
- 不解答题目
- 金句只能提供情感鼓励和学习节奏提醒
"""


async def generate_personalized_quote(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Generate a personalized quote for a student."""
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        from app.middleware.error_handler import StudentNotFound
        raise StudentNotFound()

    from datetime import date

    student_name = student.nickname or "孩子"
    grade = student.grade or "高中生"
    subjects = student.elective_subjects or ""
    subject_list = subjects.split(",") if subjects else []

    today = date.today()
    month = today.month

    phase_desc = _get_phase_description(grade, month)

    context = f"""
学生名字：{student_name}
年级：{grade}
选考科目：{subjects or '未选择'}
当前阶段：{phase_desc}
当前月份：{month}月
"""

    system_prompt = build_system_prompt(QUOTE_GENERATION_SYSTEM_PROMPT)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请为以下学生生成一条个性化金句：\n{context}"},
    ]

    try:
        response = await llm_client.chat(messages, json_mode=True, max_tokens=256)
        import json

        content = response["content"]
        quote_data = json.loads(content)
        return {
            "content": quote_data.get("content", ""),
            "author": quote_data.get("author", "AI家长顾问"),
            "category": "personalized",
        }
    except Exception as exc:
        logger.error("Failed to generate personalized quote: %s", exc)
        return {
            "content": f"{student_name}的每一天，都在书写属于自己的精彩。",
            "author": "AI家长顾问",
            "category": "personalized",
        }


def _get_phase_description(grade: str, month: int) -> str:
    """Get a description of the current study phase."""
    if grade == "gao3":
        if month in (9, 10, 11):
            return "一轮复习阶段"
        elif month in (12, 1):
            return "一模备考阶段"
        elif month in (2, 3):
            return "二轮复习阶段"
        elif month in (4, 5):
            return "冲刺阶段"
        elif month == 6:
            return "高考月"
        else:
            return "暑假休整期"
    elif grade == "gao2":
        if month in (9, 10, 11, 12):
            return "新课学习阶段"
        elif month in (1, 2):
            return "期末备考阶段"
        elif month in (3, 4, 5, 6):
            return "新课+复习阶段"
        else:
            return "暑假阶段"
    else:
        if month in (9, 10, 11, 12):
            return "适应高中阶段"
        elif month in (1, 2):
            return "期末备考阶段"
        elif month in (3, 4, 5, 6):
            return "打基础阶段"
        else:
            return "暑假阶段"
