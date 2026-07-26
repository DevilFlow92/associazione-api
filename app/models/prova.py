from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.indirizzo import Indirizzo
    from app.models.servizio import Servizio


class Prova(Base):
    """Prova musicale, orientata a un Servizio o standalone.

    ``servizio_id`` valorizzato indica una prova in preparazione a quel
    servizio (concerto/evento); nullo indica una prova standalone (es. prova
    di un libretto marce appena rinnovato). ``indirizzo_id`` è nullable: a
    differenza di un Servizio (sempre confermato con un committente), una
    prova può essere organizzata rapidamente senza che il luogo sia ancora
    stato deciso.
    """

    __tablename__ = "prove"

    id: Mapped[int] = mapped_column(primary_key=True)
    banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bande.codice"), nullable=False
    )
    data_prova: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    indirizzo_id: Mapped[int | None] = mapped_column(
        ForeignKey("indirizzi.id"), nullable=True
    )
    servizio_id: Mapped[int | None] = mapped_column(
        ForeignKey("servizi.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    indirizzo: Mapped[Indirizzo | None] = relationship(
        "Indirizzo", foreign_keys=[indirizzo_id]
    )
    servizio: Mapped[Servizio | None] = relationship(
        "Servizio", foreign_keys=[servizio_id]
    )
