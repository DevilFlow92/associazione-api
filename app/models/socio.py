from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.iscrizione import Iscrizione
    from app.models.persona import Persona


class Socio(Base):
    __tablename__ = "soci"

    id: Mapped[int] = mapped_column(primary_key=True)
    codice_socio: Mapped[str] = mapped_column(String(5))
    persona_id: Mapped[int] = mapped_column(ForeignKey("persone.id"), nullable=False)
    banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bande.codice"), nullable=False
    )
    ruolo_banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("ruoli_banda.codice"), nullable=False
    )

    persona: Mapped[Persona] = relationship(back_populates="soci")
    iscrizioni: Mapped[list[Iscrizione]] = relationship(back_populates="socio")
