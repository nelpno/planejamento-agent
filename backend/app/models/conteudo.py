"""Modelo SQLAlchemy para a tabela conteudos."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Conteudo(Base):
    __tablename__ = "conteudos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    planejamento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("planejamentos.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(nullable=False)
    pilar: Mapped[str | None] = mapped_column(nullable=True)
    framework: Mapped[str | None] = mapped_column(nullable=True)
    titulo: Mapped[str] = mapped_column(nullable=False)
    conteudo: Mapped[dict] = mapped_column(JSONB, nullable=False)
    variacoes_ab: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    referencia_visual: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    planejamento = relationship("Planejamento", back_populates="conteudos")
