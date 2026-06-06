from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.socio import Socio


class StatoPagamento(StrEnum):
    NON_PAGATO = "non_pagato"
    PAGATO = "pagato"
    PARZIALE = "parziale"


class Iscrizione(Base):
    __tablename__ = "iscrizioni"

    id: Mapped[int] = mapped_column(primary_key=True)
    socio_id: Mapped[int] = mapped_column(ForeignKey("soci.id"), nullable=False)
    anno: Mapped[int] = mapped_column(nullable=False)
    quota_dovuta: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quota_pagata: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    stato_pagamento: Mapped[StatoPagamento] = mapped_column(
        String(20), default=StatoPagamento.NON_PAGATO
    )
    data_iscrizione: Mapped[date] = mapped_column(Date, default=date.today)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    socio: Mapped[Socio] = relationship(back_populates="iscrizioni")
