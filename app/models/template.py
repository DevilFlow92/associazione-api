from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Template(Base):
    """Template di documento dinamico (modulistica).

    ``contenuto_json`` è l'albero del documento prodotto dall'editor TipTap.
    ``entita_richieste`` elenca i provider di merge field necessari per
    compilarlo (es. ``["socio", "banda"]``, si veda ``app.mergefields``).
    """

    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255))
    descrizione: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contenuto_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    entita_richieste: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    creato_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    aggiornato_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
