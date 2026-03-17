import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.context import PipelineContext
from app.providers.openrouter_client import OpenRouterClient
from app.utils.json_parser import parse_json_safe as _parse_json_safe


class BaseAgent(ABC):
    name: str = "base_agent"

    def __init__(self, client: OpenRouterClient):
        self.client = client
        self._on_progress: Callable[..., Awaitable[Any]] | None = None

    async def run(self, context: PipelineContext) -> PipelineContext:
        start_time = time.time()
        context.current_status = f"running_{self.name}"
        try:
            context = await self.execute(context)
            duration_ms = int((time.time() - start_time) * 1000)
            context.log_decision(
                self.name,
                f"{self.name} completed in {duration_ms}ms",
                self._get_completion_reasoning(context),
            )
        except Exception as e:
            context.log_decision(
                self.name,
                f"{self.name} failed: {str(e)}",
                f"Error: {type(e).__name__}",
            )
            raise
        return context

    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext: ...

    def _get_completion_reasoning(self, context: PipelineContext) -> str:
        return f"{self.name} executed successfully"

    @staticmethod
    def parse_json_safe(response: str) -> dict:
        """Parse JSON from LLM response with fallback for markdown-wrapped JSON."""
        return _parse_json_safe(response)
