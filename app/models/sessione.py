from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.utente import Utente


class Sessione(Base):
    """Sessione server-side di un utente umano.

    L'autenticazione umana è basata su sessioni revocabili: il client riceve un
    token opaco (cookie) di cui il DB conserva solo l'hash SHA-256. Una sessione
    è valida finché non scade (``scade_il``) e non viene revocata
    (``revocata_il`` nullo).
    """

    __tablename__ = "sessioni"

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id"), nullable=False, index=True
    )
    # SHA-256 esadecimale del token opaco: il token in chiaro non è mai persistito.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    creata_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    scade_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revocata_il: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    utente: Mapped[Utente] = relationship(back_populates="sessioni")
