import logging
import uuid
from datetime import datetime, timezone

from app.agents.context import PipelineContext
from app.agents.gerador import GeradorAgent
from app.providers.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the planning pipeline: Gerador with auto-research via tool use."""

    def __init__(self, session_factory=None):
        self.client = OpenRouterClient()
        self.gerador = GeradorAgent(self.client)
        self._session_factory = session_factory

        # Passa callback de progresso para o Gerador (WebSocket em tempo real)
        self.gerador._on_progress = self._save_progress

    async def run(self, context: PipelineContext) -> PipelineContext:
        """Execute the pipeline: Gerador com auto-research via tools."""
        context.started_at = datetime.now(timezone.utc).isoformat()
        context.current_status = "em_geracao"

        try:
            logger.info("[%s] Starting Gerador (with auto-research)", context.planejamento_id)
            context = await self.gerador.run(context)
            await self._save_progress(context, "gerador")

            context.completed_at = datetime.now(timezone.utc).isoformat()
            context.current_status = "concluido"

        except Exception as e:
            context.current_status = "failed"
            context.completed_at = datetime.now(timezone.utc).isoformat()
            logger.exception("[%s] Pipeline failed: %s", context.planejamento_id, str(e))
            raise
        finally:
            await self.client.close()

        return context

    async def _save_progress(self, context: PipelineContext, step: str):
        """Persist pipeline progress to the database."""
        if not self._session_factory:
            return

        from app.models.pipeline_log import PipelineLog

        try:
            async with self._session_factory() as session:
                log_entry = PipelineLog(
                    planejamento_id=uuid.UUID(context.planejamento_id) if isinstance(context.planejamento_id, str) else context.planejamento_id,
                    agent_name=step,
                    iteration=1,
                    decision=context.decision_log[-1].decision if context.decision_log else step,
                    reasoning=context.decision_log[-1].reasoning if context.decision_log else "",
                )
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            logger.error("[%s] Failed to save progress for '%s': %s", context.planejamento_id, step, str(e))
