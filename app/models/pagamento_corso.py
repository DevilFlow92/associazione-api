from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.iscrizione_corso import IscrizioneCorso
    from app.models.ricevuta import Ricevuta


class PagamentoCorso(Base):
    """Pagamento di una quota corso da parte di una Persona iscritta.

    Alla creazione genera automaticamente una ``Ricevuta`` (RISCOSSIONE) e un
    ``FlussoCassa`` (AUTO_PAGAMENTO_CORSO), sul pattern di auto-posting già
    usato da ``Iscrizione``/AUTO_ISCRIZIONE per le quote associative — vedi
    ``PagamentoCorsoService``. ``ricevuta_id`` è nullable per simmetria con
    ``Iscrizione.ricevuta_id`` ma in pratica è sempre valorizzato dal service
    alla creazione, essendo la ricevuta generata automaticamente e non
    caricata manualmente in un secondo momento.
    """

    __tablename__ = "pagamenti_corso"

    id: Mapped[int] = mapped_column(primary_key=True)
    iscrizione_corso_id: Mapped[int] = mapped_column(
        ForeignKey("iscrizioni_corso.id"), nullable=False
    )
    data_pagamento: Mapped[date] = mapped_column(Date, nullable=False)
    importo: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    ricevuta_id: Mapped[int | None] = mapped_column(
        ForeignKey("ricevute.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    iscrizione_corso: Mapped[IscrizioneCorso] = relationship(
        "IscrizioneCorso", foreign_keys=[iscrizione_corso_id]
    )
    ricevuta: Mapped[Ricevuta | None] = relationship(
        "Ricevuta", foreign_keys=[ricevuta_id]
    )
