"""Schemas Pydantic para Conteudo."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConteudoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    planejamento_id: UUID
    tipo: str
    pilar: str | None = None
    framework: str | None = None
    titulo: str
    conteudo: dict
    variacoes_ab: list | None = None
    referencia_visual: str | None = None
    ordem: int
    created_at: datetime
