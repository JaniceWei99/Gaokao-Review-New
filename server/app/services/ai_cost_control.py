"""AI token cost control — rate limiting, usage tracking, and caching."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone

from app.services.cache_service import cache_get, cache_set

logger = logging.getLogger(__name__)

DAILY_CHAT_KEY = "ai:chat_count:{user_id}:{date}"
DAILY_TOKEN_KEY = "ai:token_usage:{user_id}:{date}"
SIMILAR_QUESTION_KEY = "ai:similar:{hash}"


async def check_daily_chat_limit(user_id: str, limit: int = 10) -> tuple[bool, int]:
    """Check if user has exceeded daily chat limit.

    Returns:
        (is_within_limit, current_count)
    """
    today = date.today().isoformat()
    key = DAILY_CHAT_KEY.format(user_id=user_id, date=today)
    cached = await cache_get(key)
    count = cached if isinstance(cached, int) else 0
    return count < limit, count


async def increment_chat_count(user_id: str) -> int:
    """Increment daily chat count. Returns new count."""
    today = date.today().isoformat()
    key = DAILY_CHAT_KEY.format(user_id=user_id, date=today)
    cached = await cache_get(key)
    count = (cached if isinstance(cached, int) else 0) + 1
    await cache_set(key, count, ttl=86400 * 2)
    return count


async def track_token_usage(user_id: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Track daily token usage for cost monitoring."""
    today = date.today().isoformat()
    key = DAILY_TOKEN_KEY.format(user_id=user_id, date=today)
    cached = await cache_get(key)
    usage = cached if isinstance(cached, dict) else {"prompt": 0, "completion": 0}
    usage["prompt"] = usage.get("prompt", 0) + prompt_tokens
    usage["completion"] = usage.get("completion", 0) + completion_tokens
    await cache_set(key, usage, ttl=86400 * 2)


async def get_cached_similar_response(question_hash: str) -> str | None:
    """Check if a similar question has been answered before."""
    key = SIMILAR_QUESTION_KEY.format(hash=question_hash)
    cached = await cache_get(key)
    return cached if isinstance(cached, str) else None


async def cache_similar_response(question_hash: str, response: str) -> None:
    """Cache a response for similar questions (TTL 7 days)."""
    key = SIMILAR_QUESTION_KEY.format(hash=question_hash)
    await cache_set(key, response, ttl=86400 * 7)


def simple_hash(text: str) -> str:
    """Simple hash for question similarity check."""
    import hashlib

    normalized = text.strip().lower()
    return hashlib.md5(normalized.encode()).hexdigest()[:12]
