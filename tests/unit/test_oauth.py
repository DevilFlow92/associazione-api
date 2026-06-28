from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.oauth_account import OAuthAccount
from app.models.ruolo import Ruolo
from app.models.utente import TipoUtente, Utente


async def _seed_ospite_ruolo(db: AsyncSession) -> Ruolo:
    ruolo = Ruolo(nome="Ospite", banda_codice=None)
    db.add(ruolo)
    await db.commit()
    await db.refresh(ruolo)
    return ruolo


async def _seed_user(db: AsyncSession, email: str) -> Utente:
    utente = Utente(
        tipo=TipoUtente.UMANO,
        email=email,
        password_hash=hash_password("secret123"),
        attivo=True,
        superuser=False,
    )
    db.add(utente)
    await db.commit()
    await db.refresh(utente)
    return utente


# ── OAuthService unit tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_oauth_new_user_creates_ospite(db_session: AsyncSession):
    """Un provider sconosciuto con email nuova crea un Utente con ruolo Ospite."""
    from app.repositories.oauth_account_repository import OAuthAccountRepository
    from app.repositories.ruolo_repository import RuoloRepository
    from app.repositories.sessione_repository import SessioneRepository
    from app.repositories.utente_repository import UtenteRepository
    from app.services.auth_service import AuthService
    from app.services.oauth_service import OAuthService

    await _seed_ospite_ruolo(db_session)

    utente_repo = UtenteRepository(db_session)
    oauth_repo = OAuthAccountRepository(db_session)
    sessione_repo = SessioneRepository(db_session)
    ruolo_repo = RuoloRepository(db_session)
    auth_service = AuthService(utente_repo, sessione_repo)
    service = OAuthService(
        utente_repo, oauth_repo, sessione_repo, ruolo_repo, auth_service
    )

    token = await service.login_or_register(
        provider="google",
        provider_user_id="google-uid-001",
        email="newuser@example.com",
        nome_completo="New User",
    )
    assert token  # session token returned

    # Utente creato
    utente = await utente_repo.get_by_email("newuser@example.com")
    assert utente is not None
    assert utente.tipo == TipoUtente.UMANO

    # OAuthAccount creato
    oauth = await oauth_repo.get_by_provider("google", "google-uid-001")
    assert oauth is not None
    assert oauth.utente_id == utente.id


@pytest.mark.asyncio
async def test_oauth_links_existing_user_by_email(db_session: AsyncSession):
    """Un provider con email già esistente linka l'account senza creare
    un nuovo utente."""
    from app.repositories.oauth_account_repository import OAuthAccountRepository
    from app.repositories.ruolo_repository import RuoloRepository
    from app.repositories.sessione_repository import SessioneRepository
    from app.repositories.utente_repository import UtenteRepository
    from app.services.auth_service import AuthService
    from app.services.oauth_service import OAuthService

    existing = await _seed_user(db_session, "existing@example.com")

    utente_repo = UtenteRepository(db_session)
    oauth_repo = OAuthAccountRepository(db_session)
    sessione_repo = SessioneRepository(db_session)
    ruolo_repo = RuoloRepository(db_session)
    auth_service = AuthService(utente_repo, sessione_repo)
    service = OAuthService(
        utente_repo, oauth_repo, sessione_repo, ruolo_repo, auth_service
    )

    token = await service.login_or_register(
        provider="google",
        provider_user_id="google-uid-002",
        email="existing@example.com",
        nome_completo="Existing User",
    )
    assert token

    oauth = await oauth_repo.get_by_provider("google", "google-uid-002")
    assert oauth is not None
    assert oauth.utente_id == existing.id  # linked to existing user, not new


@pytest.mark.asyncio
async def test_oauth_returning_user(db_session: AsyncSession):
    """Un provider già noto (OAuthAccount esistente) apre sessione
    senza creare niente."""
    from app.repositories.oauth_account_repository import OAuthAccountRepository
    from app.repositories.ruolo_repository import RuoloRepository
    from app.repositories.sessione_repository import SessioneRepository
    from app.repositories.utente_repository import UtenteRepository
    from app.services.auth_service import AuthService
    from app.services.oauth_service import OAuthService

    existing = await _seed_user(db_session, "returning@example.com")
    oauth_account = OAuthAccount(
        utente_id=existing.id,
        provider="google",
        provider_user_id="google-uid-003",
        email="returning@example.com",
    )
    db_session.add(oauth_account)
    await db_session.commit()

    utente_repo = UtenteRepository(db_session)
    oauth_repo = OAuthAccountRepository(db_session)
    sessione_repo = SessioneRepository(db_session)
    ruolo_repo = RuoloRepository(db_session)
    auth_service = AuthService(utente_repo, sessione_repo)
    service = OAuthService(
        utente_repo, oauth_repo, sessione_repo, ruolo_repo, auth_service
    )

    token = await service.login_or_register(
        provider="google",
        provider_user_id="google-uid-003",
        email="returning@example.com",
        nome_completo="Returning User",
    )
    assert token
