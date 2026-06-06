from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.documento import Documento
    from app.models.iscrizione import Iscrizione


class StatoSocio(StrEnum):
    ATTIVO = "attivo"
    SOSPESO = "sospeso"
    CESSATO = "cessato"


class Socio(Base):
    __tablename__ = "soci"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    cognome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    data_nascita: Mapped[date | None] = mapped_column(Date, nullable=True)
    strumento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stato: Mapped[StatoSocio] = mapped_column(String(20), default=StatoSocio.ATTIVO)
    deleted_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    iscrizioni: Mapped[list[Iscrizione]] = relationship(back_populates="socio")
    documenti: Mapped[list[Documento]] = relationship(back_populates="socio")
