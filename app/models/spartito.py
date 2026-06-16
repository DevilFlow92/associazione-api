from __future__ import annotations

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Spartito(Base):
    """Partitura archiviata, collegata a un Documento (il PDF).

    ``strumento_codice`` nullo indica un PDF unico che contiene tutte le parti
    strumentali. ``scaffale``/``ripiano``/``cartella`` localizzano la copia
    cartacea in archivio (facoltativi).
    """

    __tablename__ = "spartiti"

    id: Mapped[int] = mapped_column(primary_key=True)
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
