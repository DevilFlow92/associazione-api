from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.corso import Corso
    from app.models.indirizzo import Indirizzo


class Lezione(Base):
    """Sessione datata di un Corso: calendario e registro presenze.

    ``corso_id`` è obbligatoria: a differenza di Prova (standalone o
    orientata a un Servizio), una Lezione appartiene sempre a un Corso.
    ``indirizzo_id`` è nullable, stesso discorso di Prova/Servizio dopo
    l'ultima card di hardening: la sede può non essere ancora decisa.
    """

    __tablename__ = "lezioni"

    id: Mapped[int] = mapped_column(primary_key=True)
    corso_id: Mapped[int] = mapped_column(ForeignKey("corsi.id"), nullable=False)
    data_lezione: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    indirizzo_id: Mapped[int | None] = mapped_column(
        ForeignKey("indirizzi.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    corso: Mapped[Corso] = relationship("Corso", foreign_keys=[corso_id])
    indirizzo: Mapped[Indirizzo | None] = relationship(
        "Indirizzo", foreign_keys=[indirizzo_id]
    )
