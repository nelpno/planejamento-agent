import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OpenRouterClient:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.http_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://planejamento-agent.local",
                "X-Title": "Planejamento Agent",
            },
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0),
            http2=True,
        )

    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 8192,
        response_format: dict | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        data = await self._request_with_retry(payload)
        return data["choices"][0]["message"]["content"]

    async def _request_with_retry(self, payload: dict) -> dict:
        """Send request with retry logic for rate limits and timeouts."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = await self.http_client.post("/chat/completions", json=payload)
                if response.status_code == 429:
                    if attempt < max_attempts - 1:
                        wait = 2 ** attempt
                        logger.warning("Rate limited (429), retrying in %ds (attempt %d/%d)", wait, attempt + 1, max_attempts)
                        await asyncio.sleep(wait)
                        continue
                    response.raise_for_status()
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                if attempt < max_attempts - 1:
                    wait = 2 ** attempt
                    logger.warning("Timeout, retrying in %ds (attempt %d/%d)", wait, attempt + 1, max_attempts)
                    await asyncio.sleep(wait)
                else:
                    raise
        raise RuntimeError(f"OpenRouter request failed after {max_attempts} attempts")

    async def chat_with_tools(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict],
        tool_executor: Callable[[str, dict], Awaitable[str]],
        temperature: float = 0.7,
        max_tokens: int = 12288,
        thinking: dict | None = None,
        max_tool_rounds: int = 5,
    ) -> tuple[str, list[dict]]:
        """Chat with tool use loop.

        Args:
            tools: tool definitions in OpenAI format
            tool_executor: async callback (tool_name, arguments) -> result_string
            thinking: extended thinking config (Phase 2), e.g. {"type": "enabled", "budget_tokens": 8000}
            max_tool_rounds: max tool use rounds before aborting

        Returns:
            (final_content, tool_calls_history)
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "tools": tools,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if thinking:
            payload["thinking"] = thinking

        tool_history: list[dict] = []

        for round_num in range(max_tool_rounds):
            data = await self._request_with_retry(payload)
            message = data["choices"][0]["message"]

            tool_calls = message.get("tool_calls")
            if not tool_calls:
                return message.get("content") or "", tool_history

            # Append assistant message with tool calls to conversation
            payload["messages"].append(message)

            for tc in tool_calls:
                func = tc["function"]
                name = func["name"]
                args = json.loads(func["arguments"]) if isinstance(func["arguments"], str) else func["arguments"]

                logger.info("Tool call [round %d]: %s(%s)", round_num + 1, name, json.dumps(args, ensure_ascii=False)[:100])
                tool_history.append({"name": name, "arguments": args, "id": tc["id"]})

                result = await tool_executor(name, args)

                payload["messages"].append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

        raise RuntimeError(f"Tool use loop exceeded {max_tool_rounds} rounds")

    async def close(self):
        await self.http_client.aclose()
