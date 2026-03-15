import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.cliente import Cliente
from app.models.planejamento import Planejamento
from app.models.conteudo import Conteudo
from app.models.historico_temas import HistoricoTemas
from app.schemas.planejamento import (
    PlanejamentoCreate,
    PlanejamentoResponse,
    PlanejamentoListItem,
    PlanejamentoUpdate,
)
from app.schemas.conteudo import ConteudoResponse
from app.services.storage_service import get_pdf_path

router = APIRouter(prefix="/api/planejamentos", tags=["planejamentos"])


@router.post("", response_model=PlanejamentoResponse, status_code=201)
async def create_planejamento(
    data: PlanejamentoCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new planejamento and kick off the generation pipeline."""
    # Validate client exists
    result = await session.execute(
        select(Cliente).where(Cliente.id == data.cliente_id)
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # Create planejamento record
    planejamento = Planejamento(
        cliente_id=data.cliente_id,
        mes_referencia=data.mes_referencia,
        inputs_extras=data.inputs_extras,
        status="em_geracao",
    )
    session.add(planejamento)
    await session.commit()  # Fix #2: commit before Celery dispatch to avoid race condition

    # Get historical themes (last 3 months)
    hist_result = await session.execute(
        select(HistoricoTemas)
        .where(HistoricoTemas.cliente_id == data.cliente_id)
        .order_by(HistoricoTemas.mes.desc())
        .limit(3)
    )
    historico = hist_result.scalars().all()
    historico_temas = [
        {"mes": h.mes, "temas": h.temas, "notas": h.notas}
        for h in historico
    ]

    # Build pipeline context
    tipos_conteudo = data.tipos_conteudo_override or cliente.tipos_conteudo or []
    from app.agents.context import PipelineContext, ClienteData

    context = PipelineContext(
        planejamento_id=str(planejamento.id),
        cliente=ClienteData(
            id=str(cliente.id),
            nome_empresa=cliente.nome_empresa,
            nicho=cliente.nicho,
            publico_alvo=cliente.publico_alvo or {},
            tom_de_voz=cliente.tom_de_voz or {},
            pilares=cliente.pilares or [],
            tipos_conteudo=tipos_conteudo,
            concorrentes=cliente.concorrentes or [],
            instrucoes=cliente.instrucoes,
        ),
        mes_referencia=data.mes_referencia,
        inputs_extras=data.inputs_extras,
        tipos_conteudo_override=data.tipos_conteudo_override,
        historico_temas=historico_temas,
    )

    # Dispatch Celery task
    from app.tasks.generation_tasks import generate_planejamento_task
    generate_planejamento_task.delay(
        str(planejamento.id),
        context.to_dict(),
    )

    return planejamento


@router.get("", response_model=list[PlanejamentoListItem])
async def list_planejamentos(
    cliente_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
):
    query = select(Planejamento).order_by(Planejamento.created_at.desc())
    if cliente_id:
        query = query.where(Planejamento.cliente_id == cliente_id)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.get("/{planejamento_id}", response_model=PlanejamentoResponse)
async def get_planejamento(
    planejamento_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Planejamento).where(Planejamento.id == planejamento_id)
    )
    planejamento = result.scalar_one_or_none()
    if not planejamento:
        raise HTTPException(status_code=404, detail="Planejamento não encontrado")
    return planejamento


@router.get("/{planejamento_id}/conteudos", response_model=list[ConteudoResponse])
async def get_conteudos(
    planejamento_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Conteudo)
        .where(Conteudo.planejamento_id == planejamento_id)
        .order_by(Conteudo.ordem)
    )
    return list(result.scalars().all())


@router.post("/{planejamento_id}/aprovar")
async def aprovar_planejamento(
    planejamento_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Planejamento).where(Planejamento.id == planejamento_id)
    )
    planejamento = result.scalar_one_or_none()
    if not planejamento:
        raise HTTPException(status_code=404, detail="Planejamento não encontrado")

    planejamento.status = "aprovado"

    # Save themes to history
    if planejamento.temas:
        temas_list = [t.get("tema", "") for t in planejamento.temas if isinstance(t, dict)]
        historico = HistoricoTemas(
            cliente_id=planejamento.cliente_id,
            mes=planejamento.mes_referencia,
            temas=temas_list,
        )
        session.add(historico)

    return {"status": "aprovado"}


@router.post("/{planejamento_id}/ajustar")
async def ajustar_planejamento(
    planejamento_id: uuid.UUID,
    data: PlanejamentoUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Planejamento).where(Planejamento.id == planejamento_id)
    )
    planejamento = result.scalar_one_or_none()
    if not planejamento:
        raise HTTPException(status_code=404, detail="Planejamento não encontrado")

    planejamento.status = "em_geracao"
    planejamento.feedback = data.feedback

    # Re-dispatch pipeline with feedback
    result = await session.execute(
        select(Cliente).where(Cliente.id == planejamento.cliente_id)
    )
    cliente = result.scalar_one_or_none()

    hist_result = await session.execute(
        select(HistoricoTemas)
        .where(HistoricoTemas.cliente_id == planejamento.cliente_id)
        .order_by(HistoricoTemas.mes.desc())
        .limit(3)
    )
    historico = hist_result.scalars().all()
    historico_temas = [
        {"mes": h.mes, "temas": h.temas, "notas": h.notas}
        for h in historico
    ]

    from app.agents.context import PipelineContext, ClienteData
    context = PipelineContext(
        planejamento_id=str(planejamento.id),
        cliente=ClienteData(
            id=str(cliente.id),
            nome_empresa=cliente.nome_empresa,
            nicho=cliente.nicho,
            publico_alvo=cliente.publico_alvo or {},
            tom_de_voz=cliente.tom_de_voz or {},
            pilares=cliente.pilares or [],
            tipos_conteudo=cliente.tipos_conteudo or [],
            concorrentes=cliente.concorrentes or [],
            instrucoes=cliente.instrucoes,
        ),
        mes_referencia=planejamento.mes_referencia,
        inputs_extras=f"{planejamento.inputs_extras or ''}\n\nFEEDBACK DO OPERADOR:\n{data.feedback}",
        historico_temas=historico_temas,
    )

    await session.commit()  # Fix #2: commit before dispatch

    from app.tasks.generation_tasks import generate_planejamento_task
    generate_planejamento_task.delay(str(planejamento.id), context.to_dict())

    return {"status": "em_geracao", "message": "Planejamento sendo refeito com feedback"}


@router.get("/{planejamento_id}/download")
async def download_pdf(
    planejamento_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Planejamento).where(Planejamento.id == planejamento_id)
    )
    planejamento = result.scalar_one_or_none()
    if not planejamento or not planejamento.pdf_url:
        raise HTTPException(status_code=404, detail="PDF não encontrado")

    filename = planejamento.pdf_url.split("/")[-1]
    filepath = get_pdf_path(filename)
    if not filepath:
        raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado")

    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=f"planejamento-{planejamento.mes_referencia}.pdf",
    )
