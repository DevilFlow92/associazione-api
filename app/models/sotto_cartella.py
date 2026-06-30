from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.macro_sezione import MacroSezione


class SottoCartella(Base):
    """Sotto-cartella personalizzabile dall'utente dentro una macro-sezione.

    A differenza della macro-sezione (fissa, seedata), queste sono create,
    rinominate ed eliminate liberamente dall'utente con permesso di scrittura
    sulla macro-sezione genitrice.
    """

    __tablename__ = "sotto_cartelle"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    macro_sezione_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("macro_sezioni.codice"), nullable=False
    )

    macro_sezione: Mapped[MacroSezione] = relationship(
        "MacroSezione", back_populates="sotto_cartelle"
    )
