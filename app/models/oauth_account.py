from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.utente import Utente


class OAuthAccount(Base):
    """Provider OAuth2 collegato a un Utente.

    Un utente può avere più account OAuth (uno per provider).
    Il campo `provider_user_id` è l'identificatore univoco restituito
    dal provider (es. Google `sub`, Apple `sub`, Facebook `id`).
    """

    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_uid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(
        ForeignKey("utenti.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # "google" | "apple" | "facebook"
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # email dal provider, informativa
    creato_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    utente: Mapped[Utente] = relationship(back_populates="oauth_accounts")
