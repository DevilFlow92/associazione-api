from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.committente import Committente
    from app.models.indirizzo import Indirizzo
    from app.models.ricevuta import Ricevuta


class Servizio(Base):
    """Servizio della banda (concerto, processione, evento).

    ``indirizzo_id`` è nullable, come per ``Prova``: un servizio può essere
    organizzato rapidamente senza che il luogo sia ancora stato deciso, e
    l'indirizzo essere confermato in un secondo momento.
    """

    __tablename__ = "servizi"

    id: Mapped[int] = mapped_column(primary_key=True)
    banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bande.codice"), nullable=False
    )
    anno: Mapped[int] = mapped_column(Integer, nullable=False)
    descrizione_servizio: Mapped[str] = mapped_column(String(255))
    data_servizio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    indirizzo_id: Mapped[int | None] = mapped_column(
        ForeignKey("indirizzi.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    committente_id: Mapped[int | None] = mapped_column(
        ForeignKey("committenti.id"), nullable=True
    )
    referente: Mapped[str | None] = mapped_column(String(255), nullable=True)
    compenso_pattuito: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    indirizzo: Mapped[Indirizzo | None] = relationship(
        "Indirizzo", foreign_keys=[indirizzo_id]
    )
    committente: Mapped[Committente | None] = relationship(
        "Committente", foreign_keys=[committente_id]
    )
    ricevute: Mapped[list[Ricevuta]] = relationship(back_populates="servizio")
