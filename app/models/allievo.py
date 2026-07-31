from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.indirizzo import Indirizzo
    from app.models.persona import Persona


class Allievo(Base):
    __tablename__ = "allievi"

    id: Mapped[int] = mapped_column(primary_key=True)
    codice_allievo: Mapped[str] = mapped_column(String(5))
    persona_id: Mapped[int] = mapped_column(
        ForeignKey("persone.id"), nullable=False, unique=True
    )
    indirizzo_id: Mapped[int | None] = mapped_column(
        ForeignKey("indirizzi.id"), nullable=True
    )

    persona: Mapped[Persona] = relationship(back_populates="allievo")
    indirizzo: Mapped[Indirizzo | None] = relationship(
        "Indirizzo", foreign_keys=[indirizzo_id]
    )
