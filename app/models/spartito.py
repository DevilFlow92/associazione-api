from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.documento import Documento
    from app.models.lookups import Strumento, TipoSpartito


class Spartito(Base):
    """Partitura archiviata, collegata a un Documento (il PDF).

    ``strumento_codice`` nullo indica un PDF unico che contiene tutte le parti
    strumentali. ``scaffale``/``ripiano``/``cartella`` localizzano la copia
    cartacea in archivio (facoltativi).
    """

    __tablename__ = "spartiti"

    id: Mapped[int] = mapped_column(primary_key=True)
    banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bande.codice"), nullable=False
    )
    tipo_spartito_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("tipi_spartito.codice"), nullable=False
    )
    strumento_codice: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("strumenti.codice"), nullable=True
    )
    documento_id: Mapped[int] = mapped_column(
        ForeignKey("documenti.id"), nullable=False
    )
    scaffale: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ripiano: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cartella: Mapped[str | None] = mapped_column(String(50), nullable=True)

    tipo_spartito: Mapped[TipoSpartito] = relationship(
        "TipoSpartito", foreign_keys=[tipo_spartito_codice]
    )
    strumento: Mapped[Strumento | None] = relationship(
        "Strumento", foreign_keys=[strumento_codice]
    )
    documento: Mapped[Documento] = relationship(
        "Documento", foreign_keys=[documento_id]
    )
