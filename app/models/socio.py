from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.iscrizione import Iscrizione
    from app.models.lookups import RuoloBanda, Strumento
    from app.models.persona import Persona


class Socio(Base):
    __tablename__ = "soci"

    id: Mapped[int] = mapped_column(primary_key=True)
    codice_socio: Mapped[str] = mapped_column(String(5))
    persona_id: Mapped[int] = mapped_column(ForeignKey("persone.id"), nullable=False)
    ruolo_banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("ruoli_banda.codice"), nullable=False
    )
    strumento_codice: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("strumenti.codice"), nullable=True
    )

    persona: Mapped[Persona] = relationship(back_populates="soci")
    ruolo_banda: Mapped[RuoloBanda] = relationship(
        "RuoloBanda", foreign_keys=[ruolo_banda_codice]
    )
    strumento: Mapped[Strumento | None] = relationship(
        "Strumento", foreign_keys=[strumento_codice]
    )
    iscrizioni: Mapped[list[Iscrizione]] = relationship(back_populates="socio")
