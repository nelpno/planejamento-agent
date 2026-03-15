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
        foco=data.foco,
        destino_conversao=data.destino_conversao,
        tipo_conteudo_uso=data.tipo_conteudo_uso,
        plataformas=data.plataformas,
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
        foco=data.foco,
        destino_conversao=data.destino_conversao,
        tipo_conteudo_uso=data.tipo_conteudo_uso,
        plataformas=data.plataformas or [],
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
    limit: int = 100,  # max 500 via validation
    session: AsyncSession = Depends(get_session),
):
    query = select(Planejamento).order_by(Planejamento.created_at.desc())
    if cliente_id:
        query = query.where(Planejamento.cliente_id == cliente_id)
    query = query.limit(limit)
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

    await session.commit()

    return {"status": "aprovado"}


@router.post("/{planejamento_id}/regerar")
async def regerar_planejamento(
    planejamento_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Re-run the FULL pipeline from scratch (Pesquisador → Estrategista → Planejador → Revisor)."""
    result = await session.execute(
        select(Planejamento).where(Planejamento.id == planejamento_id)
    )
    planejamento = result.scalar_one_or_none()
    if not planejamento:
        raise HTTPException(status_code=404, detail="Planejamento não encontrado")

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

    tipos_conteudo = cliente.tipos_conteudo or []

    planejamento.status = "em_geracao"
    planejamento.feedback = None

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
        mes_referencia=planejamento.mes_referencia,
        inputs_extras=planejamento.inputs_extras,
        historico_temas=historico_temas,
        foco=planejamento.foco,
        destino_conversao=planejamento.destino_conversao,
        tipo_conteudo_uso=planejamento.tipo_conteudo_uso,
        plataformas=planejamento.plataformas or [],
    )

    await session.commit()

    from app.tasks.generation_tasks import generate_planejamento_task
    generate_planejamento_task.delay(str(planejamento.id), context.to_dict())

    return {"status": "em_geracao", "message": "Regenerando planejamento completo"}


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

    # Load client data
    result = await session.execute(
        select(Cliente).where(Cliente.id == planejamento.cliente_id)
    )
    cliente = result.scalar_one_or_none()

    # Load existing conteudos to pass to Ajustador
    conteudos_result = await session.execute(
        select(Conteudo).where(Conteudo.planejamento_id == planejamento_id).order_by(Conteudo.ordem)
    )
    conteudos_existentes = conteudos_result.scalars().all()

    from app.agents.context import PipelineContext, ClienteData, ConteudoGerado
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
        inputs_extras=data.feedback,  # Feedback goes as input for Ajustador
        foco=planejamento.foco,
        destino_conversao=planejamento.destino_conversao,
        tipo_conteudo_uso=planejamento.tipo_conteudo_uso,
        plataformas=planejamento.plataformas or [],
        # Pass existing conteudos so Ajustador can modify them
        conteudos=[
            ConteudoGerado(
                tipo=c.tipo,
                pilar=c.pilar or "",
                framework=c.framework or "",
                titulo=c.titulo,
                conteudo=c.conteudo,
                variacoes_ab=c.variacoes_ab or [],
                referencia_visual=c.referencia_visual or "",
                ordem=c.ordem,
            )
            for c in conteudos_existentes
        ],
    )

    await session.commit()

    # Use ajustar task (Ajustador + Revisor) instead of full pipeline
    from app.tasks.generation_tasks import ajustar_planejamento_task
    ajustar_planejamento_task.delay(str(planejamento.id), context.to_dict())

    return {"status": "em_geracao", "message": "Ajustando planejamento com feedback (Ajustador + Revisor)"}


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


@router.get("/{planejamento_id}/download-docx")
async def download_docx(
    planejamento_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Download planejamento as editable DOCX."""
    from fastapi.responses import Response

    result = await session.execute(
        select(Planejamento).where(Planejamento.id == planejamento_id)
    )
    planejamento = result.scalar_one_or_none()
    if not planejamento:
        raise HTTPException(status_code=404, detail="Planejamento não encontrado")

    # Get client info
    result = await session.execute(
        select(Cliente).where(Cliente.id == planejamento.cliente_id)
    )
    cliente = result.scalar_one_or_none()

    # Get conteudos
    conteudos_result = await session.execute(
        select(Conteudo).where(Conteudo.planejamento_id == planejamento_id).order_by(Conteudo.ordem)
    )
    conteudos = conteudos_result.scalars().all()

    from app.services.docx_service import generate_planejamento_docx

    cliente_dict = {
        "nome_empresa": cliente.nome_empresa if cliente else "Cliente",
    }
    planejamento_dict = {
        "mes_referencia": planejamento.mes_referencia,
        "resumo_estrategico": planejamento.resumo_estrategico,
        "temas": planejamento.temas,
        "calendario": planejamento.calendario,
    }
    conteudos_list = [
        {
            "tipo": c.tipo,
            "pilar": c.pilar,
            "framework": c.framework,
            "titulo": c.titulo,
            "conteudo": c.conteudo,
            "variacoes_ab": c.variacoes_ab,
        }
        for c in conteudos
    ]

    docx_bytes = generate_planejamento_docx(cliente_dict, planejamento_dict, conteudos_list)

    filename = f"planejamento-{planejamento.mes_referencia}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
