from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, SmallInteger, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.iscrizione import Iscrizione
    from app.models.lookups import NaturaFlusso
    from app.models.voce_contabilita import VoceContabilita


class TipoFlussoCassa(enum.StrEnum):
    MOVIMENTO = "MOVIMENTO"
    SALDO_INIZIALE = "SALDO_INIZIALE"
    TRASFERIMENTO_USCITA = "TRASFERIMENTO_USCITA"
    TRASFERIMENTO_ENTRATA = "TRASFERIMENTO_ENTRATA"
    AUTO_ISCRIZIONE = "AUTO_ISCRIZIONE"


class FlussoCassa(Base):
    __tablename__ = "flussi_cassa"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_registrazione: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    descrizione_operazione: Mapped[str] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    voce_contabilita_id: Mapped[int] = mapped_column(
        ForeignKey("voci_contabilita.id"), nullable=False
    )
    importo: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    segno: Mapped[str] = mapped_column(String(5))
    natura_flusso_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("nature_flusso.codice"), nullable=False
    )
    tipo: Mapped[TipoFlussoCassa] = mapped_column(
        Enum(TipoFlussoCassa, name="tipo_flusso_cassa"),
        nullable=False,
        default=TipoFlussoCassa.MOVIMENTO,
        server_default=TipoFlussoCassa.MOVIMENTO.value,
    )
    iscrizione_id: Mapped[int | None] = mapped_column(
        ForeignKey("iscrizioni.id", name="fk_flussi_cassa_iscrizione_id"),
        nullable=True,
    )
    trasferimento_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )

    voce_contabilita: Mapped[VoceContabilita] = relationship(
        back_populates="flussi", lazy="selectin"
    )
    natura_flusso: Mapped[NaturaFlusso] = relationship(
        "NaturaFlusso",
        foreign_keys=[natura_flusso_codice],
        lazy="selectin",
    )
    iscrizione: Mapped[Iscrizione | None] = relationship()
