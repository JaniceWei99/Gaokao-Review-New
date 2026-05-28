"""LLM client — unified interface for AI model calls."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI-compatible LLM client (works with DashScope, OpenAI, etc.)."""

    def __init__(self) -> None:
        self._api_key = settings.llm_api_key
        self._base_url = settings.llm_base_url
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens
        self._temperature = settings.llm_temperature
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
            return self._client
        except ImportError:
            logger.error("openai package not installed")
            raise

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> dict[str, Any]:
        """Send a chat completion request and return the response.

        Returns:
            {"content": str, "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}}
        """
        client = self._get_client()

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature or self._temperature,
            "max_tokens": max_tokens or self._max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        start = time.time()
        try:
            response = await client.chat.completions.create(**kwargs)
            elapsed = time.time() - start

            choice = response.choices[0] if response.choices else None
            content = choice.message.content if choice else ""

            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            logger.info(
                "LLM chat: model=%s tokens=%s elapsed=%.2fs",
                self._model,
                usage.get("total_tokens", 0),
                elapsed,
            )

            return {"content": content, "usage": usage}
        except Exception as exc:
            elapsed = time.time() - start
            logger.error("LLM chat error: %s (%.2fs)", exc, elapsed)
            raise

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        """Stream a chat completion response, yielding content chunks."""
        client = self._get_client()

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature or self._temperature,
            "max_tokens": max_tokens or self._max_tokens,
            "stream": True,
        }

        try:
            response = await client.chat.completions.create(**kwargs)
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as exc:
            logger.error("LLM stream error: %s", exc)
            raise


llm_client = LLMClient()
