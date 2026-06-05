"""MiniMax M2.7 streaming LLM client."""
import asyncio
import json
from typing import AsyncGenerator

import httpx

from app.application.chat.ports import LLMClient
from loguru import logger


class MiniMaxClient:
    """Async streaming client for MiniMax OpenAI-compatible chat completions API.

    Supports SSE streaming and MiniMax function-calling protocol.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    async def stream_chat(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> AsyncGenerator[dict, None]:
        """Send a streaming chat request and yield parsed SSE events.

        Args:
            messages: OpenAI-compatible message list.
            tools: OpenAI-compatible tool definitions.

        Yields:
            Parsed event dicts from the SSE stream.
        """
        logger.debug("[llm] MiniMax request: model={} messages={}", self._model, len(messages))
        try:
            async with self._client.stream(
                "POST",
                "/chat/completions",
                json={
                    "model": self._model,
                    "messages": messages,
                    "tools": tools,
                    "stream": True,
                    "max_tokens": self._max_tokens,
                    "temperature": self._temperature,
                },
            ) as resp:
                logger.debug("[llm] Stream started: model={}", self._model)
                if not resp.is_success:
                    await resp.aread()
                    resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        if line.strip():
                            logger.warning("[llm] Non-data SSE line ignored: {}", line[:200])
                        continue
                    payload = line.removeprefix("data: ").strip()
                    if payload == "[DONE]":
                        logger.debug("[llm] SSE [DONE] marker received")
                        break
                    try:
                        event = json.loads(payload)
                    except json.JSONDecodeError:
                        logger.warning("[llm] Failed to parse SSE payload: {}", payload[:200])
                        continue
                    logger.debug(
                        "[llm] SSE event: choices_count={} delta_keys={} msg_keys={}",
                        len(event.get("choices", [])),
                        list(event["choices"][0].get("delta", {}).keys()) if event.get("choices") else [],
                        list(event["choices"][0].get("message", {}).keys()) if event.get("choices") else [],
                    )
                    yield event
        except httpx.HTTPStatusError as exc:
            body_text = exc.response.text[:500]
            logger.error(
                "[llm] MiniMax HTTP error: status={} body={}", exc.response.status_code, body_text
            )
            raise
        except httpx.RequestError as exc:
            logger.error("[llm] MiniMax connection error: {}", exc)
            raise
        except BaseException as exc:
            if isinstance(exc, (asyncio.CancelledError, KeyboardInterrupt)):
                raise
            logger.exception("[llm] Unexpected error in MiniMax client: {}", exc)
            raise

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
