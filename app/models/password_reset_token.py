from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PasswordResetToken(Base):
    """Token monouso per il reset password di un utente umano.

    Persistiamo solo l'hash SHA-256 del token (come per le sessioni): anche con
    accesso al DB il token in chiaro non è ricostruibile. Il token scade dopo
    ``scade_il`` e, una volta usato, ``usato_il`` viene valorizzato per impedirne
    il riutilizzo.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utenti.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    scade_il: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usato_il: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
