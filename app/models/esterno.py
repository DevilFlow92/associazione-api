from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lookups import Strumento
    from app.models.persona import Persona


class Esterno(Base):
    __tablename__ = "esterni"

    id: Mapped[int] = mapped_column(primary_key=True)
    codice_esterno: Mapped[str] = mapped_column(String(5))
    strumento_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("strumenti.codice"), nullable=False
    )
    persona_id: Mapped[int] = mapped_column(ForeignKey("persone.id"), nullable=False)

    persona: Mapped[Persona] = relationship(back_populates="esterni")
    strumento: Mapped[Strumento] = relationship(
        "Strumento", foreign_keys=[strumento_codice]
    )
