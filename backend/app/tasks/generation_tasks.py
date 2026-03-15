import asyncio
import logging
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from sqlalchemy import delete as sql_delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.context import PipelineContext
from app.agents.orchestrator import PipelineOrchestrator
from app.database import AsyncSessionLocal
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="generate_planejamento")
def generate_planejamento_task(self, planejamento_id: str, pipeline_context_dict: dict):
    """Celery task that runs the full planning pipeline."""
    return asyncio.run(
        _run_pipeline(self, planejamento_id, pipeline_context_dict)
    )


@celery_app.task(bind=True, name="ajustar_planejamento")
def ajustar_planejamento_task(self, planejamento_id: str, pipeline_context_dict: dict):
    """Celery task that runs Ajustador + Revisor (without re-researching)."""
    return asyncio.run(
        _run_ajuste_pipeline(self, planejamento_id, pipeline_context_dict)
    )


async def _run_pipeline(task, planejamento_id: str, pipeline_context_dict: dict):
    """Async pipeline execution."""
    session_factory = AsyncSessionLocal

    try:
        await _update_planejamento_status(
            session_factory, planejamento_id, "em_geracao"
        )

        context = PipelineContext.from_dict(pipeline_context_dict)

        # Fix #10: Pass session_factory to orchestrator instead of creating second engine
        orchestrator = PipelineOrchestrator(session_factory=session_factory)
        context = await orchestrator.run(context)

        await _save_results(session_factory, planejamento_id, context)

        logger.info(
            "Pipeline completed for planejamento %s (score: %d, iterations: %d)",
            planejamento_id,
            context.revisao.score if context.revisao else 0,
            context.iteration,
        )

        return {
            "planejamento_id": planejamento_id,
            "status": "revisao",
            "score": context.revisao.score if context.revisao else 0,
            "total_conteudos": len(context.conteudos),
            "iterations": context.iteration,
        }

    except Exception as e:
        logger.exception(
            "Pipeline failed for planejamento %s: %s", planejamento_id, str(e)
        )
        try:
            await _update_planejamento_status(
                session_factory, planejamento_id, "failed", error=str(e),
            )
        except Exception as db_err:
            logger.error("Failed to update status to failed: %s", str(db_err))
        raise

    finally:
        pass


async def _run_ajuste_pipeline(task, planejamento_id: str, pipeline_context_dict: dict):
    """Ajuste pipeline: Ajustador → Revisor (sem Pesquisador/Estrategista)."""
    session_factory = AsyncSessionLocal

    try:
        await _update_planejamento_status(session_factory, planejamento_id, "em_geracao")

        context = PipelineContext.from_dict(pipeline_context_dict)
        context.started_at = datetime.now(timezone.utc).isoformat()

        # Guard: ajuste requires existing conteudos
        if not context.conteudos:
            raise ValueError(
                "Ajuste requer conteúdos existentes. Use o pipeline completo para gerar do zero."
            )

        from app.agents.ajustador import AjustadorAgent
        from app.agents.revisor import RevisorAgent
        from app.providers.openrouter_client import OpenRouterClient

        client = OpenRouterClient()
        try:
            # Step 1: Ajustador modifica conteúdo com base no feedback
            ajustador = AjustadorAgent(client)
            context = await ajustador.run(context)

            # Step 2: Revisor valida as mudanças
            revisor = RevisorAgent(client)
            context = await revisor.run(context)

            # Apply revised contents if available
            if context.revisao and context.revisao.conteudos_revisados:
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
        finally:
            await client.close()

        context.completed_at = datetime.now(timezone.utc).isoformat()
        await _save_results(session_factory, planejamento_id, context)

        logger.info(
            "Ajuste completed for %s (score: %d)",
            planejamento_id,
            context.revisao.score if context.revisao else 0,
        )
        return {"planejamento_id": planejamento_id, "status": "revisao"}

    except Exception as e:
        logger.exception("Ajuste failed for %s: %s", planejamento_id, str(e))
        try:
            await _update_planejamento_status(session_factory, planejamento_id, "failed", error=str(e))
        except Exception:
            pass
        raise


async def _update_planejamento_status(
    session_factory, planejamento_id: str, status: str, error: str | None = None,
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

    plan_id = uuid.UUID(planejamento_id)

    # Fix #12: Calculate pipeline duration
    pipeline_duration = None
    if context.started_at:
        try:
            started = datetime.fromisoformat(context.started_at)
            pipeline_duration = (datetime.now(timezone.utc) - started).total_seconds()
        except (ValueError, TypeError):
            pass

    async with session_factory() as session:
        # Fix #4: Delete existing conteudos before inserting new ones (prevents duplication on re-run)
        await session.execute(
            sql_delete(Conteudo).where(Conteudo.planejamento_id == plan_id)
        )

        # Update planejamento with results — only overwrite strategy fields if they exist
        # (during ajuste, estrategia/pesquisa are None — don't erase existing data)
        values = {
            "status": "revisao",
            "pipeline_logs": [asdict(entry) for entry in context.decision_log],
            "pipeline_duration": pipeline_duration,
        }
        if context.estrategia:
            values["resumo_estrategico"] = context.estrategia.resumo_estrategico
            values["temas"] = context.estrategia.temas
            values["calendario"] = context.estrategia.calendario
        if context.pesquisa:
            values["pesquisa"] = asdict(context.pesquisa)

        stmt = update(Planejamento).where(Planejamento.id == plan_id).values(**values)
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
                .where(Planejamento.id == plan_id)
                .values(pdf_url=pdf_url, html_content=html)
            )
            await session.execute(stmt)
            await session.commit()

        logger.info("PDF generated: %s", pdf_url)

    except Exception as pdf_err:
        logger.error("PDF generation failed for %s: %s", planejamento_id, str(pdf_err))
