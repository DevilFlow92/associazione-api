from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.socio import Socio


class TipoDocumento(StrEnum):
    MODULO_ISCRIZIONE = "modulo_iscrizione"
    RICEVUTA = "ricevuta"
    PARTITURA = "partitura"
    ALTRO = "altro"


class Documento(Base):
    __tablename__ = "documenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255))
    tipo: Mapped[TipoDocumento] = mapped_column(String(50))
    file_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    dimensione_bytes: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(64))
    socio_id: Mapped[int | None] = mapped_column(ForeignKey("soci.id"), nullable=True)
    caricato_il: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    socio: Mapped[Socio | None] = relationship(back_populates="documenti")
