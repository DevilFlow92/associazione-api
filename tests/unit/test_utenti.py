from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.unit.test_auth import make_user, seed_permessi


async def login_superuser(client: AsyncClient, db_session: AsyncSession) -> None:
    await seed_permessi(db_session)
    await make_user(db_session, email="admin@example.com", superuser=True)
    await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "secret123"},
    )


@pytest.mark.asyncio
async def test_create_ruolo_with_permessi(
    client: AsyncClient, db_session: AsyncSession
):
    await login_superuser(client, db_session)
    resp = await client.post(
        "/api/v1/ruoli/",
        json={
            "nome": "tesoriere",
            "descrizione": "Gestione contabilità",
            "permessi": ["contabilita:read"],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["nome"] == "tesoriere"
    assert {p["codice"] for p in data["permessi"]} == {"contabilita:read"}


@pytest.mark.asyncio
async def test_create_ruolo_unknown_permesso(
    client: AsyncClient, db_session: AsyncSession
):
    await login_superuser(client, db_session)
    resp = await client.post(
        "/api/v1/ruoli/",
        json={"nome": "x", "permessi": ["non:esiste"]},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_utente_and_assign_ruolo(
    client: AsyncClient, db_session: AsyncSession
):
    await login_superuser(client, db_session)
    ruolo = await client.post(
        "/api/v1/ruoli/",
        json={"nome": "segretario", "permessi": ["utenti:read"]},
    )
    ruolo_id = ruolo.json()["id"]

    resp = await client.post(
        "/api/v1/utenti/",
        json={
            "email": "nuovo@example.com",
            "password": "pw12345",
            "nome_completo": "Nuovo Utente",
            "ruoli": [ruolo_id],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "nuovo@example.com"
    assert data["tipo"] == "umano"
    assert {r["nome"] for r in data["ruoli"]} == {"segretario"}


@pytest.mark.asyncio
async def test_create_utente_requires_password(
    client: AsyncClient, db_session: AsyncSession
):
    await login_superuser(client, db_session)
    resp = await client.post(
        "/api/v1/utenti/",
        json={"email": "nopass@example.com"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_utente_duplicate_email(
    client: AsyncClient, db_session: AsyncSession
):
    await login_superuser(client, db_session)
    payload = {"email": "dup@example.com", "password": "pw12345"}
    await client.post("/api/v1/utenti/", json=payload)
    resp = await client.post("/api/v1/utenti/", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_utente_unknown_ruolo(
    client: AsyncClient, db_session: AsyncSession
):
    await login_superuser(client, db_session)
    resp = await client.post(
        "/api/v1/utenti/",
        json={"email": "x@example.com", "password": "pw12345", "ruoli": [999]},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_set_password_then_login(client: AsyncClient, db_session: AsyncSession):
    await login_superuser(client, db_session)
    created = await client.post(
        "/api/v1/utenti/",
        json={"email": "rotate@example.com", "password": "old12345"},
    )
    utente_id = created.json()["id"]
    resp = await client.put(
        f"/api/v1/utenti/{utente_id}/password", json={"password": "new12345"}
    )
    assert resp.status_code == 200

    # Dopo il cambio password, la nuova credenziale consente il login.
    await client.post("/api/v1/auth/logout")
    good = await client.post(
        "/api/v1/auth/login",
        json={"email": "rotate@example.com", "password": "new12345"},
    )
    assert good.status_code == 200


@pytest.mark.asyncio
async def test_list_permessi(client: AsyncClient, db_session: AsyncSession):
    await login_superuser(client, db_session)
    resp = await client.get("/api/v1/permessi/")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total_items"] >= 1
