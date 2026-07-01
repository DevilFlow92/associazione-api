from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.nome_parte import NomeParte


@pytest.fixture
async def seeded_nome_parte(db_session: AsyncSession) -> NomeParte:
    obj = NomeParte(nome="Inno alla Gioia", tipo_spartito_codice=1, banda_codice=1)
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    return obj


@pytest.mark.asyncio
async def test_create_nome_parte(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/nome-parti/",
        json={"nome": "Bolero", "tipo_spartito_codice": 1, "banda_codice": 1},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["nome"] == "Bolero"
    assert "id" in data


@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=False,
    reason="SQLite does not enforce FK constraints; expects 409 against PostgreSQL",
)
async def test_create_nome_parte_tipo_spartito_not_found(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/nome-parti/",
        json={"nome": "Inizio", "tipo_spartito_codice": 9999, "banda_codice": 1},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_get_nome_parte_not_found(client: AsyncClient) -> None:
    r = await client.get("/api/v1/nome-parti/99999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_nome_parti_empty(client: AsyncClient) -> None:
    r = await client.get("/api/v1/nome-parti/?banda_codice=1")
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_list_nome_parti_filtro_tipo(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/nome-parti/",
        json={"nome": "Primo", "tipo_spartito_codice": 1, "banda_codice": 1},
    )
    await client.post(
        "/api/v1/nome-parti/",
        json={"nome": "Secondo", "tipo_spartito_codice": 2, "banda_codice": 1},
    )
    r = await client.get("/api/v1/nome-parti/?banda_codice=1&tipo_spartito_codice=1")
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["tipo_spartito_codice"] == 1


@pytest.mark.asyncio
async def test_update_nome_parte(
    client: AsyncClient, seeded_nome_parte: NomeParte
) -> None:
    r = await client.patch(
        f"/api/v1/nome-parti/{seeded_nome_parte.id}",
        json={"nome": "Inno Aggiornato"},
    )
    assert r.status_code == 200
    assert r.json()["nome"] == "Inno Aggiornato"


@pytest.mark.asyncio
async def test_delete_nome_parte(
    client: AsyncClient, seeded_nome_parte: NomeParte
) -> None:
    r = await client.delete(f"/api/v1/nome-parti/{seeded_nome_parte.id}")
    assert r.status_code == 204
    assert (
        await client.get(f"/api/v1/nome-parti/{seeded_nome_parte.id}")
    ).status_code == 404


@pytest.mark.asyncio
async def test_delete_nome_parte_cascades_to_spartiti(client: AsyncClient) -> None:
    np_r = await client.post(
        "/api/v1/nome-parti/",
        json={"nome": "Da Eliminare", "tipo_spartito_codice": 1, "banda_codice": 1},
    )
    assert np_r.status_code == 201
    np_id = np_r.json()["id"]

    s_r = await client.post(
        "/api/v1/spartiti/",
        json={"nome_parte_id": np_id, "banda_codice": 1, "tipo_spartito_codice": 1},
    )
    assert s_r.status_code == 201
    spartito_id = s_r.json()["id"]

    del_r = await client.delete(f"/api/v1/nome-parti/{np_id}")
    assert del_r.status_code == 204

    assert (await client.get(f"/api/v1/spartiti/{spartito_id}")).status_code == 404
