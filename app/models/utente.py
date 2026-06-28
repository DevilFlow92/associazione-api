from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.relations import utenti_ruoli

if TYPE_CHECKING:
    from app.models.oauth_account import OAuthAccount
    from app.models.persona import Persona
    from app.models.ruolo import Ruolo
    from app.models.sessione import Sessione


class TipoUtente(enum.StrEnum):
    """Piano di autenticazione di un utente.

    - ``umano``: persona reale, login con email + password, sessioni server-side.
    - ``servizio``: service account macchina-a-macchina, autenticazione via JWT
      stateless (worker, bot, import massivi).
    """

    UMANO = "umano"
    SERVIZIO = "servizio"


class Utente(Base):
    """Principal autenticabile — umano o service account.

    Modello unico così l'RBAC (ruoli/permessi) si applica a entrambi i piani.
    Tutti gli utenti portano un ``password_hash`` (bcrypt): per gli umani è la
    password di login, per i service account è il client-secret usato una sola
    volta all'endpoint ``/auth/token`` per ottenere il JWT.
    """

    __tablename__ = "utenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[TipoUtente] = mapped_column(
        Enum(TipoUtente, name="tipo_utente"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # bcrypt hash; nullo per i service account (autenticati via JWT).
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nome_completo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attivo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Superuser: bypassa il controllo dei permessi.
    superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Collegamento opzionale all'anagrafica (un utente umano è spesso una persona).
    persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("persone.id"), nullable=True
    )
    creato_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    aggiornato_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    ruoli: Mapped[list[Ruolo]] = relationship(
        secondary=utenti_ruoli, back_populates="utenti", lazy="selectin"
    )
    persona: Mapped[Persona | None] = relationship()
    sessioni: Mapped[list[Sessione]] = relationship(
        back_populates="utente", cascade="all, delete-orphan"
    )
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        back_populates="utente", cascade="all, delete-orphan"
    )

    @property
    def permessi(self) -> set[str]:
        """Insieme dei codici permesso effettivi, derivati dai ruoli."""
        return {p.codice for ruolo in self.ruoli for p in ruolo.permessi}
