from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.relations import persone_indirizzi

if TYPE_CHECKING:
    from app.models.contatto import Contatto
    from app.models.esterno import Esterno
    from app.models.indirizzo import Indirizzo
    from app.models.socio import Socio


class Persona(Base):
    __tablename__ = "persone"

    id: Mapped[int] = mapped_column(primary_key=True)
    banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bande.codice"), nullable=False
    )
    cognome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ragione_sociale: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comune_nascita_codice: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("comuni.codice"), nullable=True
    )
    data_nascita: Mapped[date | None] = mapped_column(Date, nullable=True)
    codice_fiscale: Mapped[str | None] = mapped_column(String(50), nullable=True)

    contatti: Mapped[list[Contatto]] = relationship(
        back_populates="persona", cascade="all, delete-orphan"
    )
    soci: Mapped[list[Socio]] = relationship(back_populates="persona")
    esterni: Mapped[list[Esterno]] = relationship(back_populates="persona")
    indirizzi: Mapped[list[Indirizzo]] = relationship(
        secondary=persone_indirizzi, back_populates="persone"
    )
