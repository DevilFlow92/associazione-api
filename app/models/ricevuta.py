from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.esterno import Esterno
    from app.models.servizio import Servizio


class Ricevuta(Base):
    """Ricevuta emessa dall'associazione.

    Serve sia i compensi ai musicisti esterni per un servizio
    (``servizio_id`` + ``esterno_id``) sia le quote di iscrizione dei soci
    (entrambi nulli, collegata dall'iscrizione via ``ricevuta_id``).
    """

    __tablename__ = "ricevute"

    id: Mapped[int] = mapped_column(primary_key=True)
    servizio_id: Mapped[int | None] = mapped_column(
        ForeignKey("servizi.id"), nullable=True
    )
    esterno_id: Mapped[int | None] = mapped_column(
        ForeignKey("esterni.id"), nullable=True
    )
    documento_id: Mapped[int | None] = mapped_column(
        ForeignKey("documenti.id"), nullable=True
    )
    data_ricevuta: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    importo: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    note_in_stampa: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note_fuori_stampa: Mapped[str | None] = mapped_column(String(255), nullable=True)

    servizio: Mapped[Servizio | None] = relationship(back_populates="ricevute")
    esterno: Mapped[Esterno | None] = relationship("Esterno", foreign_keys=[esterno_id])
