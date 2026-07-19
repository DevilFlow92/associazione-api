from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.indirizzo import Indirizzo


class Committente(Base):
    """Ente committente di un servizio (parrocchia, comune, pro-loco, ...).

    Riutilizzabile tra più servizi: non è una ``Persona`` (non ha un
    nominativo individuale), ha una ``denominazione``. Il nominativo di
    contatto specifico per un singolo servizio vive invece su
    ``Servizio.referente``, perché cambia da servizio a servizio anche a
    parità di committente.
    """

    __tablename__ = "committenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    denominazione: Mapped[str] = mapped_column(String(255), nullable=False)
    indirizzo_id: Mapped[int | None] = mapped_column(
        ForeignKey("indirizzi.id"), nullable=True
    )
    codice_fiscale_piva: Mapped[str | None] = mapped_column(String(50), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    indirizzo: Mapped[Indirizzo | None] = relationship(
        "Indirizzo", foreign_keys=[indirizzo_id]
    )
