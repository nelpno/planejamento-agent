"""Modelo SQLAlchemy para a tabela clientes."""

import uuid
from datetime import datetime

from sqlalchemy import Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome_empresa: Mapped[str] = mapped_column(nullable=False)
    nicho: Mapped[str] = mapped_column(nullable=False)
    publico_alvo: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tom_de_voz: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pilares: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tipos_conteudo: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    concorrentes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    redes_sociais: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    instrucoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(nullable=True)
    foco_padrao: Mapped[str | None] = mapped_column(nullable=True)
    destino_padrao: Mapped[str | None] = mapped_column(nullable=True)
    tipo_uso_padrao: Mapped[str | None] = mapped_column(nullable=True)
    plataformas_padrao: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # Relationships
    planejamentos = relationship(
        "Planejamento", back_populates="cliente", cascade="all, delete-orphan"
    )
    historico_temas = relationship(
        "HistoricoTemas", back_populates="cliente", cascade="all, delete-orphan"
    )
