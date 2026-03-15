import asyncio
import logging
import uuid
from dataclasses import asdict

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.agents.context import PipelineContext
from app.agents.orchestrator import PipelineOrchestrator
from app.config import get_settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_or_create_event_loop():
    """Get the current event loop or create a new one for Celery workers."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


@celery_app.task(bind=True, name="generate_planejamento")
def generate_planejamento_task(self, planejamento_id: str, pipeline_context_dict: dict):
    """Celery task that runs the planning pipeline."""
    loop = _get_or_create_event_loop()
    return loop.run_until_complete(
        _run_pipeline(self, planejamento_id, pipeline_context_dict)
    )


async def _run_pipeline(task, planejamento_id: str, pipeline_context_dict: dict):
    """Async pipeline execution."""
    settings = get_settings()

    # Create a separate engine for Celery context
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        # Update planejamento status to "em_geracao"
        await _update_planejamento_status(
            session_factory, planejamento_id, "em_geracao"
        )

        # Build context and run pipeline
        context = PipelineContext.from_dict(pipeline_context_dict)
        orchestrator = PipelineOrchestrator(database_url=settings.DATABASE_URL)
        context = await orchestrator.run(context)

        # Save results to database
        await _save_results(session_factory, planejamento_id, context)

        logger.info(
            "Pipeline completed for planejamento %s (score: %d, iterations: %d)",
            planejamento_id,
            context.revisao.score if context.revisao else 0,
            context.iteration,
        )

        return {
            "planejamento_id": planejamento_id,
            "status": "concluido",
            "score": context.revisao.score if context.revisao else 0,
            "total_conteudos": len(context.conteudos),
            "iterations": context.iteration,
        }

    except Exception as e:
        logger.exception(
            "Pipeline failed for planejamento %s: %s", planejamento_id, str(e)
        )

        # Update status to failed
        try:
            await _update_planejamento_status(
                session_factory,
                planejamento_id,
                "failed",
                error=str(e),
            )
        except Exception as db_err:
            logger.error("Failed to update status to failed: %s", str(db_err))

        raise

    finally:
        await engine.dispose()


async def _update_planejamento_status(
    session_factory,
    planejamento_id: str,
    status: str,
    error: str | None = None,
):
    """Update planejamento status in the database."""
    from app.models.planejamento import Planejamento

    async with session_factory() as session:
        values = {"status": status}
        if error:
            values["feedback"] = f"Erro no pipeline: {error}"
        stmt = (
            update(Planejamento)
            .where(Planejamento.id == uuid.UUID(planejamento_id))
            .values(**values)
        )
        await session.execute(stmt)
        await session.commit()


async def _save_results(session_factory, planejamento_id: str, context: PipelineContext):
    """Save pipeline results to the database."""
    from app.models.conteudo import Conteudo
    from app.models.planejamento import Planejamento

    async with session_factory() as session:
        # Update planejamento with results
        plan_id = uuid.UUID(planejamento_id)
        stmt = (
            update(Planejamento)
            .where(Planejamento.id == plan_id)
            .values(
                status="revisao",
                resumo_estrategico=(
                    context.estrategia.resumo_estrategico
                    if context.estrategia
                    else None
                ),
                temas=(
                    context.estrategia.temas if context.estrategia else None
                ),
                calendario=(
                    context.estrategia.calendario if context.estrategia else None
                ),
                pesquisa=(
                    asdict(context.pesquisa) if context.pesquisa else None
                ),
                pipeline_logs=[
                    asdict(entry) for entry in context.decision_log
                ],
            )
        )
        await session.execute(stmt)

        # Save generated content pieces
        for c in context.conteudos:
            conteudo = Conteudo(
                planejamento_id=plan_id,
                tipo=c.tipo,
                pilar=c.pilar,
                framework=c.framework,
                titulo=c.titulo,
                conteudo=c.conteudo,
                variacoes_ab=c.variacoes_ab,
                referencia_visual=c.referencia_visual,
                ordem=c.ordem,
            )
            session.add(conteudo)

        await session.commit()

    # Generate PDF
    try:
        from app.services.pdf_service import render_planejamento_html, html_to_pdf, save_pdf

        cliente_dict = {
            "nome_empresa": context.cliente.nome_empresa,
            "nicho": context.cliente.nicho,
        }
        planejamento_dict = {
            "mes_referencia": context.mes_referencia,
            "resumo_estrategico": context.estrategia.resumo_estrategico if context.estrategia else "",
            "temas": context.estrategia.temas if context.estrategia else [],
            "calendario": context.estrategia.calendario if context.estrategia else [],
        }
        conteudos_list = [
            {
                "tipo": c.tipo,
                "pilar": c.pilar,
                "framework": c.framework,
                "titulo": c.titulo,
                "conteudo": c.conteudo,
                "variacoes_ab": c.variacoes_ab,
                "referencia_visual": c.referencia_visual,
            }
            for c in context.conteudos
        ]

        html = render_planejamento_html(cliente_dict, planejamento_dict, conteudos_list)
        pdf_bytes = await html_to_pdf(html)
        filename = f"planejamento-{context.cliente.nome_empresa.lower().replace(' ', '-')}-{context.mes_referencia}.pdf"
        pdf_url = await save_pdf(pdf_bytes, filename)

        async with session_factory() as session:
            stmt = (
                update(Planejamento)
                .where(Planejamento.id == uuid.UUID(planejamento_id))
                .values(pdf_url=pdf_url, html_content=html)
            )
            await session.execute(stmt)
            await session.commit()

        logger.info("PDF generated: %s", pdf_url)

    except Exception as pdf_err:
        logger.error("PDF generation failed for %s: %s", planejamento_id, str(pdf_err))
