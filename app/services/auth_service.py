from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_session_token,
    hash_session_token,
    verify_password,
)
from app.exceptions.auth import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.models.utente import TipoUtente, Utente
from app.repositories.sessione_repository import SessioneRepository
from app.repositories.utente_repository import UtenteRepository


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

    async def login(self, email: str, password: str) -> str:
        """Apre una sessione e restituisce il token opaco in chiaro."""
        utente = await self._authenticate(email, password)
        token = generate_session_token()
        scade_il = datetime.now(UTC) + timedelta(hours=settings.session_expire_hours)
        await self.sessione_repo.create(
            utente_id=utente.id,
            token_hash=hash_session_token(token),
            scade_il=scade_il,
        )
        return token

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
