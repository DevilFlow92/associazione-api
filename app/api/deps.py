"""Dipendenze di autenticazione e autorizzazione condivise dai router.

``get_current_user`` risolve il principal corrente da uno dei due piani:

- header ``Authorization: Bearer <jwt>`` → service account (macchina-a-macchina);
- cookie di sessione → utente umano.

``require_permission(codice)`` produce una dipendenza-guardia che impone un
permesso RBAC; i superuser bypassano sempre il controllo.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.exceptions.auth import InvalidTokenError
from app.models.utente import Utente
from app.repositories.oauth_account_repository import OAuthAccountRepository
from app.repositories.ruolo_repository import RuoloRepository
from app.repositories.sessione_repository import SessioneRepository
from app.repositories.utente_repository import UtenteRepository
from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService

_bearer = HTTPBearer(auto_error=False)


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UtenteRepository(db), SessioneRepository(db))


def get_oauth_service(db: AsyncSession = Depends(get_db)) -> OAuthService:
    utente_repo = UtenteRepository(db)
    sessione_repo = SessioneRepository(db)
    return OAuthService(
        utente_repo=utente_repo,
        oauth_repo=OAuthAccountRepository(db),
        sessione_repo=sessione_repo,
        ruolo_repo=RuoloRepository(db),
        auth_service=AuthService(utente_repo, sessione_repo),
    )


async def get_current_user(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    _: None = Depends(_bearer),
) -> Utente:
    """Risolve l'utente autenticato, JWT-first poi sessione cookie.

    Solleva 401 se nessuna credenziale valida è presente.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        try:
            return await auth.resolve_jwt(token)
        except InvalidTokenError as e:
            raise _unauthorized() from e

    cookie = request.cookies.get(settings.session_cookie_name)
    if cookie:
        try:
            return await auth.resolve_session(cookie)
        except InvalidTokenError as e:
            raise _unauthorized() from e

    raise _unauthorized()


def require_permission(
    codice: str,
) -> Callable[[Utente], Awaitable[Utente]]:
    """Costruisce una dipendenza che impone il possesso di un permesso."""

    async def guard(user: Utente = Depends(get_current_user)) -> Utente:
        if user.superuser or codice in user.permessi:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permesso richiesto: {codice}",
        )

    return guard


def require_superuser(user: Utente = Depends(get_current_user)) -> Utente:
    if not user.superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operazione riservata ai superuser",
        )
    return user


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticazione richiesta",
        headers={"WWW-Authenticate": "Bearer"},
    )
