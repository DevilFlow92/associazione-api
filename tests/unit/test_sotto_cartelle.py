from __future__ import annotations

from collections.abc import Collection

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.models.macro_sezione import MacroSezione
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


@pytest.fixture
async def seeded_macro_sezioni(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            MacroSezione(
                codice=1,
                nome="Certificazioni Uniche",
                permesso_prefisso="certificazioni",
                ordine=1,
            ),
            MacroSezione(
                codice=2,
                nome="Verbali e Libro Soci",
                permesso_prefisso="verbali",
                ordine=2,
            ),
            MacroSezione(
                codice=3,
                nome="Concorsi e Bandi",
                permesso_prefisso="concorsi",
                ordine=3,
            ),
            MacroSezione(
                codice=4,
                nome="Documenti Amministrativi",
                permesso_prefisso="documenti_admin",
                ordine=4,
            ),
        ]
    )
    await db_session.commit()


async def test_create_sotto_cartella_requires_write_permission(
    client: AsyncClient, seeded_macro_sezioni: None
) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"archivio:read"}
    )
    r = await client.post(
        "/api/v1/sotto-cartelle/",
        json={"nome": "Test", "macro_sezione_codice": 1},
    )
    assert r.status_code == 403
    assert "certificazioni:write" in r.json()["detail"]


async def test_create_sotto_cartella_succeeds_with_correct_permission(
    client: AsyncClient, seeded_macro_sezioni: None
) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"certificazioni:write"}
    )
    r = await client.post(
        "/api/v1/sotto-cartelle/",
        json={"nome": "Anno 2024", "macro_sezione_codice": 1},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["nome"] == "Anno 2024"
    assert data["macro_sezione_codice"] == 1
    assert "id" in data


async def test_create_sotto_cartella_succeeds_for_superuser_without_explicit_permission(
    client: AsyncClient, seeded_macro_sezioni: None
) -> None:
    # Default client is already superuser; confirm no permessi needed.
    app.dependency_overrides[get_current_user] = lambda: _user(superuser=True)
    r = await client.post(
        "/api/v1/sotto-cartelle/",
        json={"nome": "Archivio Generale", "macro_sezione_codice": 2},
    )
    assert r.status_code == 201


async def test_create_sotto_cartella_duplicate_name_same_macro_sezione_409(
    client: AsyncClient, seeded_macro_sezioni: None
) -> None:
    payload = {"nome": "Duplicato", "macro_sezione_codice": 1}
    r1 = await client.post("/api/v1/sotto-cartelle/", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/api/v1/sotto-cartelle/", json=payload)
    assert r2.status_code == 409


async def test_create_sotto_cartella_same_name_different_macro_sezione_allowed(
    client: AsyncClient, seeded_macro_sezioni: None
) -> None:
    r1 = await client.post(
        "/api/v1/sotto-cartelle/",
        json={"nome": "Condiviso", "macro_sezione_codice": 1},
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/api/v1/sotto-cartelle/",
        json={"nome": "Condiviso", "macro_sezione_codice": 2},
    )
    assert r2.status_code == 201


async def test_list_sotto_cartelle_filtered_by_macro_sezione(
    client: AsyncClient, seeded_macro_sezioni: None
) -> None:
    await client.post(
        "/api/v1/sotto-cartelle/", json={"nome": "Alpha", "macro_sezione_codice": 1}
    )
    await client.post(
        "/api/v1/sotto-cartelle/", json={"nome": "Beta", "macro_sezione_codice": 1}
    )
    await client.post(
        "/api/v1/sotto-cartelle/", json={"nome": "Gamma", "macro_sezione_codice": 2}
    )
    r = await client.get("/api/v1/sotto-cartelle/?macro_sezione_codice=1")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    assert all(item["macro_sezione_codice"] == 1 for item in items)


async def test_update_sotto_cartella_rename(
    client: AsyncClient, seeded_macro_sezioni: None
) -> None:
    created = await client.post(
        "/api/v1/sotto-cartelle/", json={"nome": "Originale", "macro_sezione_codice": 1}
    )
    sc_id = created.json()["id"]
    r = await client.patch(
        f"/api/v1/sotto-cartelle/{sc_id}", json={"nome": "Rinominata"}
    )
    assert r.status_code == 200
    assert r.json()["nome"] == "Rinominata"


async def test_delete_sotto_cartella_requires_write_permission(
    client: AsyncClient, seeded_macro_sezioni: None
) -> None:
    created = await client.post(
        "/api/v1/sotto-cartelle/",
        json={"nome": "DaEliminare", "macro_sezione_codice": 1},
    )
    sc_id = created.json()["id"]
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"archivio:read"}
    )
    r = await client.delete(f"/api/v1/sotto-cartelle/{sc_id}")
    assert r.status_code == 403


async def test_create_sotto_cartella_unknown_macro_sezione_404(
    client: AsyncClient, seeded_macro_sezioni: None
) -> None:
    r = await client.post(
        "/api/v1/sotto-cartelle/",
        json={"nome": "Orfana", "macro_sezione_codice": 999},
    )
    assert r.status_code == 404
