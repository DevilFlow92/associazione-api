from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.persona import Persona


class Contatto(Base):
    __tablename__ = "contatti"

    id: Mapped[int] = mapped_column(primary_key=True)
    ruolo_contatto_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("ruoli_contatto.codice"), nullable=False
    )
    persona_id: Mapped[int] = mapped_column(ForeignKey("persone.id"), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(100), nullable=True)

    persona: Mapped[Persona] = relationship(back_populates="contatti")
