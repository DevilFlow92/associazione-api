from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ricevuta import Ricevuta


class Servizio(Base):
    __tablename__ = "servizi"

    id: Mapped[int] = mapped_column(primary_key=True)
    banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bande.codice"), nullable=False
    )
    anno: Mapped[int] = mapped_column(Integer, nullable=False)
    descrizione_servizio: Mapped[str] = mapped_column(String(255))
    data_servizio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    indirizzo_id: Mapped[int] = mapped_column(
        ForeignKey("indirizzi.id"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ricevute: Mapped[list[Ricevuta]] = relationship(back_populates="servizio")
