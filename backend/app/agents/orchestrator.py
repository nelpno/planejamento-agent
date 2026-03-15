import logging
import uuid
from datetime import datetime, timezone

from app.agents.context import PipelineContext
from app.agents.estrategista import EstrategistaAgent
from app.agents.pesquisador import PesquisadorAgent
from app.agents.planejador import PlanejadorAgent
from app.agents.revisor import RevisorAgent
from app.providers.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the 4-agent planning pipeline with review loop."""

    # Fix #10: Accept session_factory from caller instead of creating own engine
    def __init__(self, session_factory=None):
        self.client = OpenRouterClient()
        self.pesquisador = PesquisadorAgent(self.client)
        self.estrategista = EstrategistaAgent(self.client)
        self.planejador = PlanejadorAgent(self.client)
        self.revisor = RevisorAgent(self.client)
        self._session_factory = session_factory

    async def run(self, context: PipelineContext) -> PipelineContext:
        """Execute the full pipeline: Pesquisador -> Estrategista -> Planejador -> Revisor (loop)."""
        context.started_at = datetime.now(timezone.utc).isoformat()
        context.current_status = "em_geracao"

        try:
            # Step 1: Pesquisador
            logger.info("[%s] Starting Pesquisador", context.planejamento_id)
            context = await self.pesquisador.run(context)
            await self._save_progress(context, "pesquisador")

            # Step 2: Estrategista
            logger.info("[%s] Starting Estrategista", context.planejamento_id)
            context = await self.estrategista.run(context)
            await self._save_progress(context, "estrategista")

            # Step 3 + 4: Planejador + Revisor loop
            for iteration in range(1, context.max_iterations + 1):
                context.iteration = iteration
                logger.info("[%s] Planejador (iteration %d)", context.planejamento_id, iteration)
                context = await self.planejador.run(context)
                await self._save_progress(context, "planejador")

                logger.info("[%s] Revisor (iteration %d)", context.planejamento_id, iteration)
                context = await self.revisor.run(context)
                await self._save_progress(context, "revisor")

                if context.revisao and context.revisao.aprovado:
                    # Apply revised contents only if Revisor returned ALL pieces
                    if context.revisao.conteudos_revisados and len(context.revisao.conteudos_revisados) >= len(context.conteudos):
                        from app.agents.context import ConteudoGerado
                        context.conteudos = [
                            ConteudoGerado(
                                tipo=c.get("tipo", ""),
                                pilar=c.get("pilar", ""),
                                framework=c.get("framework", ""),
                                titulo=c.get("titulo", ""),
                                conteudo=c.get("conteudo", {}),
                                variacoes_ab=c.get("variacoes_ab", []),
                                referencia_visual=c.get("referencia_visual", ""),
                                ordem=c.get("ordem", i),
                            )
                            for i, c in enumerate(context.revisao.conteudos_revisados)
                        ]
                    logger.info(
                        "[%s] Approved with score %d at iteration %d",
                        context.planejamento_id, context.revisao.score, iteration,
                    )
                    break

                if iteration < context.max_iterations:
                    logger.info(
                        "[%s] Rejected (score %d), retrying...",
                        context.planejamento_id,
                        context.revisao.score if context.revisao else 0,
                    )
                else:
                    logger.warning("[%s] Max iterations reached.", context.planejamento_id)

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
                    iteration=context.iteration,
                    decision=context.decision_log[-1].decision if context.decision_log else step,
                    reasoning=context.decision_log[-1].reasoning if context.decision_log else "",
                )
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            logger.error("[%s] Failed to save progress for '%s': %s", context.planejamento_id, step, str(e))
