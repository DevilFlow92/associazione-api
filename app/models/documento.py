from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lookups import TipoDocumento
    from app.models.sotto_cartella import SottoCartella


class Documento(Base):
    """Archivio storico dei documenti in ingresso.

    Non è legato a soci/persone: è un repository documentale classificato per
    ``tipo_documento`` (lookup). Altri aggregati (spartiti, iscrizioni,
    ricevute, template) referenziano i documenti tramite ``documento_id``.
    """

    __tablename__ = "documenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255))
    tipo_documento_codice: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("tipi_documento.codice"), nullable=True
    )
    file_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    dimensione_bytes: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(64))
    caricato_il: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )
    sotto_cartella_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sotto_cartelle.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    tipo_documento: Mapped[TipoDocumento | None] = relationship(
        "TipoDocumento", foreign_keys=[tipo_documento_codice]
    )
    sotto_cartella: Mapped[SottoCartella | None] = relationship(
        "SottoCartella", foreign_keys=[sotto_cartella_id]
    )
