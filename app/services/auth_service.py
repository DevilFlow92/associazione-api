from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.exceptions.auth import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.exceptions.utente import UtenteDuplicateEmailError
from app.models.lookups import Banda
from app.models.ruolo import Ruolo
from app.models.utente import TipoUtente, Utente
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.sessione_repository import SessioneRepository
from app.repositories.utente_repository import UtenteRepository
from app.services.email_service import (
    send_password_reset,
    send_registration_notification,
)

logger = get_logger(__name__)


class AuthService:
    """Autenticazione su due piani.

    - **Umani**: ``login`` verifica email/password e apre una sessione
      server-side, restituendo un token opaco da mettere nel cookie.
      ``resolve_session`` lo riconverte in utente.
    - **Service account**: ``issue_token`` verifica le credenziali e firma un
      JWT; ``resolve_jwt`` lo riconverte in utente.
    """

    def __init__(
        self, utente_repo: UtenteRepository, sessione_repo: SessioneRepository
    ) -> None:
        self.utente_repo = utente_repo
        self.sessione_repo = sessione_repo

    async def _authenticate(self, email: str, password: str) -> Utente:
        utente = await self.utente_repo.get_by_email(email)
        if not utente or not utente.password_hash:
            raise InvalidCredentialsError()
        if not verify_password(password, utente.password_hash):
            raise InvalidCredentialsError()
        if not utente.attivo:
            raise InactiveUserError()
        return utente

    # ── Piano umano: sessioni server-side ────────────────────────────────────

    async def _open_session(self, utente: Utente) -> str:
        """Crea una sessione server-side e restituisce il token opaco."""
        token = generate_session_token()
        scade_il = datetime.now(UTC) + timedelta(hours=settings.session_expire_hours)
        await self.sessione_repo.create(
            utente_id=utente.id,
            token_hash=hash_session_token(token),
            scade_il=scade_il,
        )
        return token

    async def login(self, email: str, password: str) -> str:
        """Apre una sessione e restituisce il token opaco in chiaro."""
        utente = await self._authenticate(email, password)
        return await self._open_session(utente)

    async def logout(self, token: str) -> None:
        sessione = await self.sessione_repo.get_by_token_hash(hash_session_token(token))
        if sessione and sessione.revocata_il is None:
            await self.sessione_repo.revoke(sessione, at=datetime.now(UTC))

    async def resolve_session(self, token: str) -> Utente:
        sessione = await self.sessione_repo.get_by_token_hash(hash_session_token(token))
        if not sessione or sessione.revocata_il is not None:
            raise InvalidTokenError()
        # Lo scade_il letto da SQLite può tornare naive: confronto in UTC.
        scade_il = sessione.scade_il
        if scade_il.tzinfo is None:
            scade_il = scade_il.replace(tzinfo=UTC)
        if scade_il < datetime.now(UTC):
            raise InvalidTokenError()
        utente = await self.utente_repo.get_by_id(sessione.utente_id)
        if not utente or not utente.attivo:
            raise InvalidTokenError()
        return utente

    # ── Piano macchina: JWT ──────────────────────────────────────────────────

    async def issue_token(self, email: str, password: str) -> tuple[str, int]:
        """Verifica le credenziali del service account e firma un JWT.

        Restituisce ``(token, expires_in_secondi)``.
        """
        utente = await self._authenticate(email, password)
        if utente.tipo is not TipoUtente.SERVIZIO:
            # I JWT sono riservati ai service account; gli umani usano /auth/login.
            raise InvalidCredentialsError()
        token = create_access_token(str(utente.id))
        return token, settings.jwt_expire_minutes * 60

    async def resolve_jwt(self, token: str) -> Utente:
        try:
            payload = decode_access_token(token)
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError() from e
        sub = payload.get("sub")
        if sub is None:
            raise InvalidTokenError()
        utente = await self.utente_repo.get_by_id(int(sub))
        if not utente or not utente.attivo:
            raise InvalidTokenError()
        return utente

    # ── Reset password (token via email) ─────────────────────────────────────

    async def request_password_reset(
        self,
        email: str,
        reset_repo: PasswordResetRepository,
    ) -> None:
        """Genera un token di reset e lo invia via email.

        Silenzioso se l'email non esiste o l'utente è disattivato: non si rivela
        se un indirizzo è registrato (anti-enumerazione).
        """
        utente = await self.utente_repo.get_by_email(email)
        if not utente or not utente.attivo:
            return
        token = secrets.token_urlsafe(32)
        scade_il = datetime.now(UTC) + timedelta(hours=1)
        await reset_repo.create(utente.id, token, scade_il)
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"
        try:
            send_password_reset(utente.email, reset_url)
        except Exception:
            # L'invio email è best-effort: non far fallire la richiesta.
            logger.warning("password reset email failed", exc_info=True)

    async def confirm_password_reset(
        self,
        token: str,
        new_password: str,
        reset_repo: PasswordResetRepository,
    ) -> bool:
        """Consuma il token e aggiorna la password. ``False`` se token invalido."""
        record = await reset_repo.consume(token)
        if not record:
            return False
        utente = await self.utente_repo.get_by_id(record.utente_id)
        if not utente:
            return False
        await self.utente_repo.set_password(utente, hash_password(new_password))
        return True

    # ── Auto-registrazione (ruolo Ospite) ────────────────────────────────────

    async def register(
        self,
        email: str,
        password: str,
        nome_completo: str | None,
        banda_codice: int,
        db: AsyncSession,
    ) -> Utente:
        """Auto-registrazione: crea un utente attivo con ruolo Ospite e notifica
        gli amministratori della banda."""
        existing = await self.utente_repo.get_by_email(email)
        if existing:
            raise UtenteDuplicateEmailError(email)

        # Ruolo Ospite globale (banda_codice NULL), seedato dalla migrazione.
        ospite_result = await db.execute(
            select(Ruolo).where(Ruolo.nome == "Ospite", Ruolo.banda_codice.is_(None))
        )
        ospite = ospite_result.scalar_one_or_none()
        if not ospite:
            raise RuntimeError("Ruolo Ospite non trovato. Eseguire le migrazioni.")

        utente = await self.utente_repo.create(
            tipo=TipoUtente.UMANO,
            email=email,
            password_hash=hash_password(password),
            nome_completo=nome_completo,
            persona_id=None,
            superuser=False,
            ruoli=[ospite],
        )

        # Notifica gli amministratori (Presidente/Vicepresidente/Segretario)
        # della banda.
        notifica_result = await db.execute(
            select(Utente)
            .join(Utente.ruoli)
            .where(
                Ruolo.nome.in_(["Presidente", "Vicepresidente", "Segretario"]),
                Ruolo.banda_codice == banda_codice,
            )
        )
        admin_utenti = notifica_result.scalars().unique().all()
        admin_emails = [u.email for u in admin_utenti if u.email]

        banda_result = await db.execute(
            select(Banda).where(Banda.codice == banda_codice)
        )
        banda = banda_result.scalar_one_or_none()
        banda_nome = banda.descrizione if banda else str(banda_codice)

        try:
            send_registration_notification(
                admin_emails, nome_completo or email, banda_nome
            )
        except Exception:
            # L'invio email è best-effort: non far fallire la registrazione.
            logger.warning("registration notification email failed", exc_info=True)

        return utente
