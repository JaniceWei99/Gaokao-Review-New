"""Redis cache service — simple get/set with TTL support."""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        logger.debug("REDIS_URL not set, caching disabled")
        return None

    try:
        import redis.asyncio as aioredis

        _redis_client = aioredis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        logger.info("Redis client created for %s", redis_url.split("@")[-1])
        return _redis_client
    except ImportError:
        logger.warning("redis package not installed, caching disabled")
        return None
    except Exception as exc:
        logger.warning("Failed to connect to Redis: %s", exc)
        return None


async def cache_get(key: str) -> dict | list | None:
    client = get_redis()
    if client is None:
        return None

    try:
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("cache_get error for %s: %s", key, exc)
        return None


async def cache_set(key: str, value: dict | list, ttl: int = 300) -> None:
    client = get_redis()
    if client is None:
        return

    try:
        await client.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=ttl)
    except Exception as exc:
        logger.warning("cache_set error for %s: %s", key, exc)


async def cache_delete(key: str) -> None:
    client = get_redis()
    if client is None:
        return

    try:
        await client.delete(key)
    except Exception as exc:
        logger.warning("cache_delete error for %s: %s", key, exc)


async def cache_delete_pattern(pattern: str) -> None:
    client = get_redis()
    if client is None:
        return

    try:
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await client.delete(*keys)
    except Exception as exc:
        logger.warning("cache_delete_pattern error for %s: %s", pattern, exc)


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception:
            pass
        _redis_client = None
