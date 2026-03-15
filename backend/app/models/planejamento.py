"""Modelo SQLAlchemy para a tabela planejamentos."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Planejamento(Base):
    __tablename__ = "planejamentos"
    __table_args__ = (
        Index("ix_planejamentos_cliente_id", "cliente_id"),
        Index("ix_planejamentos_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="CASCADE"),
        nullable=False,
    )
    mes_referencia: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        nullable=False, server_default="rascunho"
    )
    resumo_estrategico: Mapped[str | None] = mapped_column(Text, nullable=True)
    temas: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    calendario: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    inputs_extras: Mapped[str | None] = mapped_column(Text, nullable=True)
    pesquisa: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(nullable=True)
    html_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    pipeline_logs: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    pipeline_duration: Mapped[float | None] = mapped_column(nullable=True)
    foco: Mapped[str | None] = mapped_column(nullable=True)
    destino_conversao: Mapped[str | None] = mapped_column(nullable=True)
    tipo_conteudo_uso: Mapped[str | None] = mapped_column(nullable=True)
    plataformas: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # Relationships
    cliente = relationship("Cliente", back_populates="planejamentos")
    conteudos = relationship(
        "Conteudo", back_populates="planejamento", cascade="all, delete-orphan"
    )
    logs = relationship(
        "PipelineLog", back_populates="planejamento", cascade="all, delete-orphan"
    )
