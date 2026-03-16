"""Schemas Pydantic para Cliente."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClienteCreate(BaseModel):
    nome_empresa: str
    nicho: str
    publico_alvo: dict | None = None
    tom_de_voz: dict | None = None
    pilares: list[dict] | None = None
    tipos_conteudo: list[dict] | None = None
    concorrentes: list[dict] | None = None
    redes_sociais: dict | None = None
    instrucoes: str | None = None
    logo_url: str | None = None
    foco_padrao: str | None = None
    destino_padrao: str | None = None
    tipo_uso_padrao: str | None = None
    plataformas_padrao: list[str] | None = None


class KickOffInput(BaseModel):
    nome_empresa: str | None = None  # IA extrai do texto se não informado
    nicho: str | None = None  # IA extrai do texto se não informado
    kickoff_text: str = Field(..., min_length=10, max_length=20_000)


class DiscoverInput(BaseModel):
    instagram: str | None = None
    site: str | None = None
    notas: str | None = None  # Informações extras que o operador sabe


class ClienteUpdate(BaseModel):
    nome_empresa: str | None = None
    nicho: str | None = None
    publico_alvo: dict | None = None
    tom_de_voz: dict | None = None
    pilares: list[dict] | None = None
    tipos_conteudo: list[dict] | None = None
    concorrentes: list[dict] | None = None
    redes_sociais: dict | None = None
    instrucoes: str | None = None
    logo_url: str | None = None
    foco_padrao: str | None = None
    destino_padrao: str | None = None
    tipo_uso_padrao: str | None = None
    plataformas_padrao: list[str] | None = None


class ClienteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nome_empresa: str
    nicho: str
    publico_alvo: dict | None = None
    tom_de_voz: dict | None = None
    pilares: list[dict] | None = None
    tipos_conteudo: list[dict] | None = None
    concorrentes: list[dict] | None = None
    redes_sociais: dict | None = None
    instrucoes: str | None = None
    logo_url: str | None = None
    foco_padrao: str | None = None
    destino_padrao: str | None = None
    tipo_uso_padrao: str | None = None
    plataformas_padrao: list[str] | None = None
    created_at: datetime
    updated_at: datetime | None = None
