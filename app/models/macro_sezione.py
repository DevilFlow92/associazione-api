from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.sotto_cartella import SottoCartella


class MacroSezione(Base):
    """Macro-sezione fissa dell'archivio (es. Certificazioni Uniche, Verbali...).

    Seedata via migrazione, non creabile a runtime. Ogni macro-sezione porta
    un permesso RBAC dedicato (es. ``certificazioni:read``) anziché il
    generico ``archivio:read/write``.
    """

    __tablename__ = "macro_sezioni"

    codice: Mapped[int] = mapped_column(
        SmallInteger, primary_key=True, autoincrement=False
    )
    nome: Mapped[str] = mapped_column(String(100))
    permesso_prefisso: Mapped[str] = mapped_column(String(32))
    ordine: Mapped[int] = mapped_column(SmallInteger, default=0)

    sotto_cartelle: Mapped[list[SottoCartella]] = relationship(
        "SottoCartella", back_populates="macro_sezione", cascade="all, delete-orphan"
    )
