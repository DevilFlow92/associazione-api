from __future__ import annotations

from collections.abc import Collection

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.models.nome_parte import NomeParte
from app.models.permesso import Permesso
from app.models.ruolo import Ruolo
from app.models.utente import TipoUtente, Utente
from main import app


def pdf_file(filename: str = "spartito.pdf") -> tuple[str, tuple[str, bytes, str]]:
    return ("file", (filename, b"%PDF-1.4 spartito", "application/pdf"))


async def upload_documento(client: AsyncClient, filename: str = "s.pdf") -> dict:
    response = await client.post("/api/v1/documenti/", files=[pdf_file(filename)])
    assert response.status_code == 201
    return response.json()


def spartito_payload(
    tipo_spartito_codice: int,
    nome_parte_id: int,
    documento_id: int | None = None,
    **overrides: object,
) -> dict:
    payload: dict = {
        "banda_codice": 1,
        "tipo_spartito_codice": tipo_spartito_codice,
        "nome_parte_id": nome_parte_id,
    }
    if documento_id is not None:
        payload["documento_id"] = documento_id
    payload.update(overrides)
    return payload


@pytest.fixture
async def seeded_nome_parte(db_session: AsyncSession) -> NomeParte:
    obj = NomeParte(nome="Test Composizione", tipo_spartito_codice=1, banda_codice=1)
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    return obj


@pytest.mark.asyncio
async def test_create_spartito(
    client: AsyncClient, seeded_nome_parte: NomeParte
) -> None:
    doc = await upload_documento(client)
    response = await client.post(
        "/api/v1/spartiti/",
        json=spartito_payload(1, seeded_nome_parte.id, doc["id"]),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tipo_spartito_codice"] == 1
    assert data["documento_id"] == doc["id"]
    assert data["strumento_codice"] is None


@pytest.mark.asyncio
async def test_create_spartito_con_strumento_e_collocazione(
    client: AsyncClient, seeded_nome_parte: NomeParte
) -> None:
    doc = await upload_documento(client)
    response = await client.post(
        "/api/v1/spartiti/",
        json=spartito_payload(
            2,
            seeded_nome_parte.id,
            doc["id"],
            strumento_codice=5,
            scaffale="A",
            ripiano="3",
            cartella="Inni",
        ),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["strumento_codice"] == 5
    assert data["scaffale"] == "A"
    assert data["ripiano"] == "3"
    assert data["cartella"] == "Inni"


@pytest.mark.asyncio
async def test_get_spartito_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/spartiti/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_spartiti_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/spartiti/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_list_spartiti_filtro_tipo(
    client: AsyncClient, seeded_nome_parte: NomeParte
) -> None:
    doc1 = await upload_documento(client, "d1.pdf")
    doc2 = await upload_documento(client, "d2.pdf")
    await client.post(
        "/api/v1/spartiti/", json=spartito_payload(1, seeded_nome_parte.id, doc1["id"])
    )
    await client.post(
        "/api/v1/spartiti/", json=spartito_payload(2, seeded_nome_parte.id, doc2["id"])
    )
    response = await client.get("/api/v1/spartiti/?tipo_spartito_codice=1")
    assert response.json()["meta"]["total_items"] == 1


@pytest.mark.asyncio
async def test_update_spartito(
    client: AsyncClient, seeded_nome_parte: NomeParte
) -> None:
    doc = await upload_documento(client)
    created = await client.post(
        "/api/v1/spartiti/",
        json=spartito_payload(1, seeded_nome_parte.id, doc["id"]),
    )
    spartito_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/spartiti/{spartito_id}",
        json={"scaffale": "B", "ripiano": "1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scaffale"] == "B"
    assert data["ripiano"] == "1"


@pytest.mark.asyncio
async def test_delete_spartito(
    client: AsyncClient, seeded_nome_parte: NomeParte
) -> None:
    doc = await upload_documento(client)
    created = await client.post(
        "/api/v1/spartiti/",
        json=spartito_payload(1, seeded_nome_parte.id, doc["id"]),
    )
    spartito_id = created.json()["id"]
    response = await client.delete(f"/api/v1/spartiti/{spartito_id}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/spartiti/{spartito_id}")).status_code == 404


@pytest.mark.asyncio
async def test_create_spartito_without_documento(
    client: AsyncClient, seeded_nome_parte: NomeParte
) -> None:
    response = await client.post(
        "/api/v1/spartiti/",
        json=spartito_payload(1, seeded_nome_parte.id),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["documento_id"] is None
    assert data["nome_parte_id"] == seeded_nome_parte.id


# ---------------------------------------------------------------------------
# RBAC: archivio:read/write (spartiti non ha macro-sezione, permesso statico)
# ---------------------------------------------------------------------------


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
async def test_list_spartiti_requires_authentication(client: AsyncClient) -> None:
    app.dependency_overrides.pop(get_current_user, None)
    r = await client.get("/api/v1/spartiti/")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_spartiti_forbidden_without_permission(client: AsyncClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(permessi=set())
    r = await client.get("/api/v1/spartiti/")
    assert r.status_code == 403
    assert "archivio:read" in r.json()["detail"]


@pytest.mark.asyncio
async def test_list_spartiti_succeeds_with_permission(client: AsyncClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"archivio:read"}
    )
    r = await client.get("/api/v1/spartiti/")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_create_spartito_requires_authentication(
    client: AsyncClient, seeded_nome_parte: NomeParte
) -> None:
    app.dependency_overrides.pop(get_current_user, None)
    r = await client.post(
        "/api/v1/spartiti/",
        json=spartito_payload(1, seeded_nome_parte.id),
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_spartito_forbidden_without_write_permission(
    client: AsyncClient, seeded_nome_parte: NomeParte
) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"archivio:read"}
    )
    r = await client.post(
        "/api/v1/spartiti/",
        json=spartito_payload(1, seeded_nome_parte.id),
    )
    assert r.status_code == 403
    assert "archivio:write" in r.json()["detail"]


@pytest.mark.asyncio
async def test_create_spartito_succeeds_with_write_permission(
    client: AsyncClient, seeded_nome_parte: NomeParte
) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"archivio:write"}
    )
    r = await client.post(
        "/api/v1/spartiti/",
        json=spartito_payload(1, seeded_nome_parte.id),
    )
    assert r.status_code == 201
