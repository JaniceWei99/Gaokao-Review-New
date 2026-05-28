"""Compliance filter — block subject-tutoring content in AI inputs/outputs.

This module ensures AI outputs never contain:
- Subject knowledge explanations (学科知识讲解)
- Problem solutions or step-by-step answers (题目解答)
- Exam answer hints (考试答案提示)

Only parenting encouragement and study strategy advice are allowed.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

BLOCKED_INPUT_PATTERNS = [
    re.compile(r"(?:怎么|如何|为什么|解释|讲解|分析).{0,6}(?:这道题|这个题|题目|答案|解法|解题)", re.IGNORECASE),
    re.compile(r"(?:求|计算|解|证明|推导).{0,4}(?:过程|步骤|方法|答案)", re.IGNORECASE),
    re.compile(r"(?:数学|物理|化学|生物|历史|地理|政治).{0,4}(?:公式|定理|定律|原理).{0,4}(?:推导|证明|解释)", re.IGNORECASE),
    re.compile(r"(?:选择题|填空题|解答题|计算题|证明题).{0,4}(?:答案|解析|做法)", re.IGNORECASE),
]

BLOCKED_OUTPUT_PATTERNS = [
    re.compile(r"(?:步骤\s*[一二三四五1-5]|第一步|第二步|第三步).{0,20}(?:代入|计算|得出|所以|因此)", re.IGNORECASE),
    re.compile(r"(?:解[：:]).{0,10}(?:设|令|因为|由于|根据)", re.IGNORECASE),
    re.compile(r"(?:答案[是为]).{0,5}\d", re.IGNORECASE),
    re.compile(r"(?:正确答案|参考答案|标准答案).{0,5}[A-D\d]", re.IGNORECASE),
]

COMPLIANCE_SYSTEM_SUFFIX = """

【严格合规要求】
你是"高考复习助手"的AI家长顾问，不是学科辅导老师。你必须遵守以下规则：
1. 绝对不讲解任何学科知识点、公式推导、定理证明
2. 绝对不解答任何题目、不给出答案、不提供解题步骤
3. 绝对不分析试卷题目的具体解法
4. 如果用户询问学科问题，礼貌拒绝并建议咨询学校老师
5. 你只能提供：家长陪伴建议、学习节奏指导、心理鼓励、时间管理建议
6. 所有建议必须基于积极正面的教育理念，不得制造焦虑
"""


def check_input_compliance(user_message: str) -> tuple[bool, str]:
    """Check if user input is compliant.

    Returns:
        (is_compliant, reason) — if not compliant, reason explains why.
    """
    for pattern in BLOCKED_INPUT_PATTERNS:
        if pattern.search(user_message):
            return False, "您的问题涉及学科知识讲解，我无法提供题目解答或学科辅导。建议咨询学校老师获取专业指导。"

    return True, ""


def check_output_compliance(ai_response: str) -> tuple[bool, str]:
    """Check if AI output is compliant.

    Returns:
        (is_compliant, sanitized_response)
    """
    for pattern in BLOCKED_OUTPUT_PATTERNS:
        match = pattern.search(ai_response)
        if match:
            logger.warning("AI output blocked by compliance filter: %s", match.group())
            return False, "抱歉，我无法提供学科知识讲解。建议咨询学校老师获取专业指导。"

    return True, ai_response


def build_system_prompt(base_prompt: str) -> str:
    """Append compliance rules to the system prompt."""
    return base_prompt + COMPLIANCE_SYSTEM_SUFFIX
