from __future__ import annotations

from collections.abc import Collection

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user
from app.models.permesso import Permesso
from app.models.ruolo import Ruolo
from app.models.utente import TipoUtente, Utente
from main import app


def _user(*, superuser: bool = False, permessi: Collection[str] = ()) -> Utente:
    ruoli: list[Ruolo] = []
    if permessi:
        ruoli = [
            Ruolo(
                nome="test",
                permessi=[Permesso(codice=c, descrizione=c) for c in permessi],
            )
        ]
    return Utente(
        id=1,
        tipo=TipoUtente.UMANO,
        email="test@example.com",
        superuser=superuser,
        ruoli=ruoli,
    )


@pytest.mark.asyncio
async def test_create_and_get_strumento(client: AsyncClient):
    response = await client.post(
        "/api/v1/strumenti/", json={"codice": 1, "descrizione": "Flauto"}
    )
    assert response.status_code == 201
    assert response.json() == {"codice": 1, "descrizione": "Flauto"}

    response = await client.get("/api/v1/strumenti/1")
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Flauto"


@pytest.mark.asyncio
async def test_create_strumento_duplicate_codice(client: AsyncClient):
    await client.post("/api/v1/strumenti/", json={"codice": 1, "descrizione": "Flauto"})
    response = await client.post(
        "/api/v1/strumenti/", json={"codice": 1, "descrizione": "Ottavino"}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_strumento_not_found(client: AsyncClient):
    response = await client.get("/api/v1/strumenti/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_strumento(client: AsyncClient):
    await client.post("/api/v1/strumenti/", json={"codice": 1, "descrizione": "Flauto"})
    response = await client.patch(
        "/api/v1/strumenti/1", json={"descrizione": "Ottavino"}
    )
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Ottavino"


@pytest.mark.asyncio
async def test_update_strumento_not_found(client: AsyncClient):
    response = await client.patch("/api/v1/strumenti/999", json={"descrizione": "X"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_strumento(client: AsyncClient):
    await client.post("/api/v1/strumenti/", json={"codice": 1, "descrizione": "Flauto"})
    response = await client.delete("/api/v1/strumenti/1")
    assert response.status_code == 204

    response = await client.get("/api/v1/strumenti/1")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_strumenti_paginated(client: AsyncClient):
    for codice in range(1, 4):
        await client.post(
            "/api/v1/strumenti/",
            json={"codice": codice, "descrizione": f"Strumento {codice}"},
        )
    response = await client.get("/api/v1/strumenti/?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["meta"]["total_items"] == 3
    assert data["meta"]["total_pages"] == 2
    assert data["meta"]["has_next"] is True


@pytest.mark.asyncio
async def test_regione_carries_foreign_key(client: AsyncClient):
    response = await client.post(
        "/api/v1/regioni/",
        json={"codice": 1, "descrizione": "Sardegna", "stato_codice": 1},
    )
    assert response.status_code == 201
    assert response.json()["stato_codice"] == 1


@pytest.mark.asyncio
async def test_comune_carries_extra_fields(client: AsyncClient):
    response = await client.post(
        "/api/v1/comuni/",
        json={
            "codice": 5535,
            "descrizione": "Quartu Sant'Elena",
            "codice_catastale": "B354",
            "provincia_codice": 92,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["codice_catastale"] == "B354"
    assert data["provincia_codice"] == 92


@pytest.mark.asyncio
async def test_comune_codice_catastale_esatto_6_caratteri(client: AsyncClient):
    response = await client.post(
        "/api/v1/comuni/",
        json={
            "codice": 5535,
            "descrizione": "Quartu Sant'Elena",
            "codice_catastale": "B354Z",
        },
    )
    assert response.status_code == 201
    assert response.json()["codice_catastale"] == "B354Z"


@pytest.mark.asyncio
async def test_comune_codice_catastale_troppo_lungo(client: AsyncClient):
    response = await client.post(
        "/api/v1/comuni/",
        json={
            "codice": 5535,
            "descrizione": "Quartu Sant'Elena",
            "codice_catastale": "B354ZZZ",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_provincia_sigla_esatto_5_caratteri(client: AsyncClient):
    response = await client.post(
        "/api/v1/province/",
        json={"codice": 92, "descrizione": "Cagliari", "sigla": "CAGLI"},
    )
    assert response.status_code == 201
    assert response.json()["sigla"] == "CAGLI"


@pytest.mark.asyncio
async def test_provincia_sigla_troppo_lunga(client: AsyncClient):
    response = await client.post(
        "/api/v1/province/",
        json={"codice": 92, "descrizione": "Cagliari", "sigla": "CAGLIA"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_strumenti_forbidden_without_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user()
    response = await client.get("/api/v1/strumenti/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_strumenti_succeeds_with_read_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"lookup:read"})
    response = await client.get("/api/v1/strumenti/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_strumento_forbidden_without_write_permission(
    client: AsyncClient,
):
    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"lookup:read"})
    response = await client.post(
        "/api/v1/strumenti/", json={"codice": 1, "descrizione": "Flauto"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_strumento_succeeds_with_write_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"lookup:write"}
    )
    response = await client.post(
        "/api/v1/strumenti/", json={"codice": 1, "descrizione": "Flauto"}
    )
    assert response.status_code == 201
