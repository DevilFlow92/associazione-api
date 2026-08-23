from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lookups import TipoCorso


class VoceProgrammaCatalogo(Base):
    """Voce riutilizzabile del catalogo programmi (scale, tecnica, repertorio, ...).

    Il "delete" esposto dal service è un soft-delete (``attiva=False``): mai
    una DELETE fisica, per non invalidare i riferimenti storici da schede
    alunno già compilate con questa voce.
    """

    __tablename__ = "voci_programma_catalogo"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_corso_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("tipi_corso.codice"), nullable=False
    )
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    testo: Mapped[str] = mapped_column(String(200), nullable=False)
    attiva: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tipo_corso: Mapped[TipoCorso] = relationship(
        "TipoCorso", foreign_keys=[tipo_corso_codice]
    )
