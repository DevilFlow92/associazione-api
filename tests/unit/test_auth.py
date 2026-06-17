from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.permesso import Permesso
from app.models.ruolo import Ruolo
from app.models.utente import TipoUtente, Utente


async def seed_permessi(db: AsyncSession) -> None:
    for codice in (
        "utenti:read",
        "utenti:write",
        "ruoli:read",
        "ruoli:write",
        "contabilita:read",
    ):
        db.add(Permesso(codice=codice, descrizione=codice))
    await db.commit()


async def make_user(
    db: AsyncSession,
    *,
    email: str = "human@example.com",
    password: str = "secret123",
    tipo: TipoUtente = TipoUtente.UMANO,
    superuser: bool = False,
    attivo: bool = True,
    permessi: list[str] | None = None,
) -> Utente:
    utente = Utente(
        tipo=tipo,
        email=email,
        password_hash=hash_password(password),
        attivo=attivo,
        superuser=superuser,
    )
    if permessi:
        ruolo = Ruolo(nome=f"ruolo-{email}", banda_codice=None)
        ruolo.permessi = [Permesso(codice=c, descrizione=c) for c in permessi]
        utente.ruoli = [ruolo]
    db.add(utente)
    await db.commit()
    await db.refresh(utente)
    return utente


# ── Login / sessioni umane ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_sets_cookie_and_me(client: AsyncClient, db_session: AsyncSession):
    await make_user(db_session, superuser=True)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "human@example.com", "password": "secret123"},
    )
    assert resp.status_code == 200
    assert client.cookies.get("session_token")

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "human@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession):
    await make_user(db_session)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "human@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session: AsyncSession):
    await make_user(db_session, attivo=False)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "human@example.com", "password": "secret123"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_logout_revokes_session(client: AsyncClient, db_session: AsyncSession):
    await make_user(db_session, superuser=True)
    await client.post(
        "/api/v1/auth/login",
        json={"email": "human@example.com", "password": "secret123"},
    )
    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 200
    # Cookie cancellato → /me non più autenticato.
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ── JWT / service account ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_service_account_token_and_bearer(
    client: AsyncClient, db_session: AsyncSession
):
    await make_user(
        db_session,
        email="worker@example.com",
        tipo=TipoUtente.SERVIZIO,
        superuser=True,
    )
    token_resp = await client.post(
        "/api/v1/auth/token",
        json={"email": "worker@example.com", "password": "secret123"},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me.status_code == 200
    assert me.json()["tipo"] == "servizio"


@pytest.mark.asyncio
async def test_human_cannot_get_jwt(client: AsyncClient, db_session: AsyncSession):
    await make_user(db_session, tipo=TipoUtente.UMANO)
    resp = await client.post(
        "/api/v1/auth/token",
        json={"email": "human@example.com", "password": "secret123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_bearer_token(client: AsyncClient):
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert me.status_code == 401


# ── RBAC: guardie sui permessi ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_permission_denied(client: AsyncClient, db_session: AsyncSession):
    # Utente con solo contabilita:read → niente accesso a /utenti (utenti:read).
    await make_user(db_session, permessi=["contabilita:read"])
    await client.post(
        "/api/v1/auth/login",
        json={"email": "human@example.com", "password": "secret123"},
    )
    resp = await client.get("/api/v1/utenti/")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_permission_granted(client: AsyncClient, db_session: AsyncSession):
    await make_user(db_session, permessi=["utenti:read"])
    await client.post(
        "/api/v1/auth/login",
        json={"email": "human@example.com", "password": "secret123"},
    )
    resp = await client.get("/api/v1/utenti/")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_superuser_bypasses_permissions(
    client: AsyncClient, db_session: AsyncSession
):
    await make_user(db_session, superuser=True)
    await client.post(
        "/api/v1/auth/login",
        json={"email": "human@example.com", "password": "secret123"},
    )
    # Nessun permesso assegnato, ma superuser → 200.
    resp = await client.get("/api/v1/ruoli/")
    assert resp.status_code == 200
