from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.relations import bande_indirizzi, persone_indirizzi

if TYPE_CHECKING:
    from app.models.lookups import Banda
    from app.models.persona import Persona


class Indirizzo(Base):
    __tablename__ = "indirizzi"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_indirizzo_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("tipi_indirizzo.codice"), nullable=False
    )
    prima_riga: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seconda_riga: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comune_codice: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("comuni.codice"), nullable=True
    )
    cap: Mapped[str | None] = mapped_column(String(5), nullable=True)
    numero_civico: Mapped[str | None] = mapped_column(String(10), nullable=True)
    interno: Mapped[str | None] = mapped_column(String(100), nullable=True)

    persone: Mapped[list[Persona]] = relationship(
        secondary=persone_indirizzi, back_populates="indirizzi"
    )
    bande: Mapped[list[Banda]] = relationship(
        secondary=bande_indirizzi, back_populates="indirizzi"
    )
