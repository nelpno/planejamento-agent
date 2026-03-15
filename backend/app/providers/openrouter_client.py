import asyncio
import logging

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
            timeout=120.0,
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
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = await self.http_client.post("/chat/completions", json=payload)
                if response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning("Rate limited (429), retrying in %ds (attempt %d/%d)", wait, attempt + 1, max_attempts)
                    await asyncio.sleep(wait)
                    continue
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.TimeoutException:
                if attempt < max_attempts - 1:
                    wait = 2 ** attempt
                    logger.warning("Timeout, retrying in %ds (attempt %d/%d)", wait, attempt + 1, max_attempts)
                    await asyncio.sleep(wait)
                else:
                    raise
            except httpx.HTTPStatusError:
                if response.status_code == 429 and attempt < max_attempts - 1:
                    continue
                raise

        raise RuntimeError(f"OpenRouter request failed after {max_attempts} attempts")

    async def close(self):
        await self.http_client.aclose()
