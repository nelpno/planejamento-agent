import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.agents.context import PipelineContext
from app.agents.estrategista import EstrategistaAgent
from app.agents.pesquisador import PesquisadorAgent
from app.agents.planejador import PlanejadorAgent
from app.agents.revisor import RevisorAgent
from app.config import settings
from app.providers.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the 4-agent planning pipeline with review loop."""

    def __init__(self, database_url: str | None = None):
        self.client = OpenRouterClient()
        self.pesquisador = PesquisadorAgent(self.client)
        self.estrategista = EstrategistaAgent(self.client)
        self.planejador = PlanejadorAgent(self.client)
        self.revisor = RevisorAgent(self.client)

        # Separate async engine for Celery context
        db_url = database_url or settings.DATABASE_URL
        self._engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def run(self, context: PipelineContext) -> PipelineContext:
        """Execute the full pipeline: Pesquisador -> Estrategista -> Planejador -> Revisor (loop)."""
        context.started_at = datetime.now(timezone.utc).isoformat()
        context.current_status = "em_geracao"

        try:
            # Step 1: Pesquisador
            logger.info("[%s] Starting Pesquisador", context.planejamento_id)
            context = await self.pesquisador.run(context)
            await self._save_progress(context, "pesquisa_concluida")

            # Step 2: Estrategista
            logger.info("[%s] Starting Estrategista", context.planejamento_id)
            context = await self.estrategista.run(context)
            await self._save_progress(context, "estrategia_concluida")

            # Step 3 + 4: Planejador + Revisor loop
            for iteration in range(1, context.max_iterations + 1):
                context.iteration = iteration
                logger.info(
                    "[%s] Starting Planejador (iteration %d)",
                    context.planejamento_id,
                    iteration,
                )
                context = await self.planejador.run(context)
                await self._save_progress(context, f"conteudo_gerado_iter_{iteration}")

                logger.info(
                    "[%s] Starting Revisor (iteration %d)",
                    context.planejamento_id,
                    iteration,
                )
                context = await self.revisor.run(context)
                await self._save_progress(context, f"revisao_iter_{iteration}")

                if context.revisao and context.revisao.aprovado:
                    logger.info(
                        "[%s] Content approved with score %d at iteration %d",
                        context.planejamento_id,
                        context.revisao.score,
                        iteration,
                    )
                    break

                if iteration < context.max_iterations:
                    logger.info(
                        "[%s] Content rejected (score %d), retrying...",
                        context.planejamento_id,
                        context.revisao.score if context.revisao else 0,
                    )
                else:
                    logger.warning(
                        "[%s] Max iterations reached. Using last output.",
                        context.planejamento_id,
                    )

            context.completed_at = datetime.now(timezone.utc).isoformat()
            context.current_status = "concluido"

        except Exception as e:
            context.current_status = "failed"
            context.completed_at = datetime.now(timezone.utc).isoformat()
            logger.exception(
                "[%s] Pipeline failed: %s", context.planejamento_id, str(e)
            )
            raise
        finally:
            await self.close()

        return context

    async def _save_progress(self, context: PipelineContext, step: str):
        """Persist pipeline progress to the database."""
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
            logger.error(
                "[%s] Failed to save progress for step '%s': %s",
                context.planejamento_id,
                step,
                str(e),
            )

    async def close(self):
        """Clean up resources."""
        await self.client.close()
        await self._engine.dispose()
