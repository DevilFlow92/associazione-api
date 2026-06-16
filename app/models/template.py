from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.documento import Documento


class Template(Base):
    """Template documentale: metadati su un Documento archiviato.

    Base del futuro sistema di documenti dinamici (configuratore campi a
    frontend). Il file vive su ``documenti``; il template ne è una vista con
    nome e descrizione applicativi.
    """

    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    documento_id: Mapped[int] = mapped_column(
        ForeignKey("documenti.id"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(255))
    descrizione: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creato_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    aggiornato_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    documento: Mapped[Documento] = relationship()
