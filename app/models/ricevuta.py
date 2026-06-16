from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.servizio import Servizio


class Ricevuta(Base):
    __tablename__ = "ricevute"

    id: Mapped[int] = mapped_column(primary_key=True)
    servizio_id: Mapped[int] = mapped_column(ForeignKey("servizi.id"), nullable=False)
    esterno_id: Mapped[int] = mapped_column(ForeignKey("esterni.id"), nullable=False)
    data_ricevuta: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    importo: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    note_in_stampa: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note_fuori_stampa: Mapped[str | None] = mapped_column(String(255), nullable=True)

    servizio: Mapped[Servizio] = relationship(back_populates="ricevute")
