from __future__ import annotations

from collections.abc import Collection

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.models.permesso import Permesso
from app.models.ruolo import Ruolo
from app.models.sotto_cartella import SottoCartella
from app.models.utente import TipoUtente, Utente
from main import app


@pytest.fixture
async def seeded_sotto_cartella(
    seeded_macro_sezioni: None, db_session: AsyncSession
) -> int:
    sc = SottoCartella(nome="Cartella Template", macro_sezione_codice=1)
    db_session.add(sc)
    await db_session.commit()
    await db_session.refresh(sc)
    return sc.id


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


def template_payload(**overrides) -> dict:
    payload = {
        "nome": "Modulo Iscrizione",
        "contenuto_json": {"type": "doc", "content": []},
        "entita_richieste": ["socio", "banda"],
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_template(client: AsyncClient):
    response = await client.post("/api/v1/templates/", json=template_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Modulo Iscrizione"
    assert data["descrizione"] is None
    assert data["contenuto_json"] == {"type": "doc", "content": []}
    assert data["entita_richieste"] == ["socio", "banda"]
    assert data["sotto_cartella_id"] is None
    assert "creato_il" in data


@pytest.mark.asyncio
async def test_create_template_con_sotto_cartella_id(
    client: AsyncClient, seeded_sotto_cartella: int
):
    response = await client.post(
        "/api/v1/templates/",
        json=template_payload(sotto_cartella_id=seeded_sotto_cartella),
    )
    assert response.status_code == 201
    assert response.json()["sotto_cartella_id"] == seeded_sotto_cartella


@pytest.mark.asyncio
async def test_update_template_sotto_cartella_id(
    client: AsyncClient, seeded_sotto_cartella: int
):
    created = await client.post("/api/v1/templates/", json=template_payload())
    template_id = created.json()["id"]
    assert created.json()["sotto_cartella_id"] is None

    response = await client.patch(
        f"/api/v1/templates/{template_id}",
        json={"sotto_cartella_id": seeded_sotto_cartella},
    )
    assert response.status_code == 200
    assert response.json()["sotto_cartella_id"] == seeded_sotto_cartella


@pytest.mark.asyncio
async def test_create_template_con_descrizione(client: AsyncClient):
    response = await client.post(
        "/api/v1/templates/",
        json=template_payload(
            nome="Ricevuta Base", descrizione="Template per le ricevute ai soci"
        ),
    )
    assert response.status_code == 201
    assert response.json()["descrizione"] == "Template per le ricevute ai soci"


@pytest.mark.asyncio
async def test_get_template_not_found(client: AsyncClient):
    response = await client.get("/api/v1/templates/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_templates_empty(client: AsyncClient):
    response = await client.get("/api/v1/templates/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient):
    await client.post("/api/v1/templates/", json=template_payload(nome="T1"))
    await client.post("/api/v1/templates/", json=template_payload(nome="T2"))
    response = await client.get("/api/v1/templates/")
    assert response.json()["meta"]["total_items"] == 2


@pytest.mark.asyncio
async def test_update_template(client: AsyncClient):
    created = await client.post(
        "/api/v1/templates/", json=template_payload(nome="Originale")
    )
    template_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/templates/{template_id}",
        json={"nome": "Aggiornato", "descrizione": "Nuova desc"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Aggiornato"
    assert data["descrizione"] == "Nuova desc"


@pytest.mark.asyncio
async def test_delete_template(client: AsyncClient):
    created = await client.post(
        "/api/v1/templates/", json=template_payload(nome="Da cancellare")
    )
    template_id = created.json()["id"]
    response = await client.delete(f"/api/v1/templates/{template_id}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/templates/{template_id}")).status_code == 404


@pytest.mark.asyncio
async def test_list_templates_forbidden_without_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user()
    response = await client.get("/api/v1/templates/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_templates_succeeds_with_read_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"templates:read"}
    )
    response = await client.get("/api/v1/templates/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_template_forbidden_without_write_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"templates:read"}
    )
    response = await client.post("/api/v1/templates/", json=template_payload())
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_template_succeeds_with_write_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"templates:write"}
    )
    response = await client.post("/api/v1/templates/", json=template_payload())
    assert response.status_code == 201
