"""Schemas Pydantic para Planejamento."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanejamentoCreate(BaseModel):
    cliente_id: UUID
    mes_referencia: str
    inputs_extras: str | None = None
    tipos_conteudo_override: list[dict] | None = None
    foco: str | None = None  # geração_leads, vendas_ecommerce, crescimento_organico, branding, lancamento, retencao
    destino_conversao: str | None = None  # whatsapp, site, dm_instagram, loja_online, agendamento, telefone
    tipo_conteudo_uso: str | None = None  # organico, pago, ambos
    plataformas: list[str] | None = None  # ["instagram", "tiktok", "youtube", "linkedin", "facebook"]


class PlanejamentoUpdate(BaseModel):
    status: str | None = None
    resumo_estrategico: str | None = None
    temas: list[dict] | None = None
    calendario: list[dict] | None = None
    inputs_extras: str | None = None
    pesquisa: dict | None = None
    feedback: str | None = None
    pdf_url: str | None = None
    html_content: str | None = None
    pipeline_logs: list[dict] | None = None
    pipeline_duration: float | None = None


class PlanejamentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cliente_id: UUID
    mes_referencia: str
    status: str
    resumo_estrategico: str | None = None
    temas: list[dict] | None = None
    calendario: list[dict] | None = None
    inputs_extras: str | None = None
    pesquisa: dict | None = None
    feedback: str | None = None
    pdf_url: str | None = None
    html_content: str | None = None
    pipeline_logs: list[dict] | None = None
    pipeline_duration: float | None = None
    foco: str | None = None
    destino_conversao: str | None = None
    tipo_conteudo_uso: str | None = None
    plataformas: list[str] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class PlanejamentoListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cliente_id: UUID
    mes_referencia: str
    status: str
    created_at: datetime
