from __future__ import annotations

import os
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


def pdf_file(filename: str = "test.pdf") -> tuple[str, tuple[str, bytes, str]]:
    content = b"%PDF-1.4 test pdf content"
    return ("file", (filename, content, "application/pdf"))


def fake_file(filename: str = "test.txt") -> tuple[str, tuple[str, bytes, str]]:
    return ("file", (filename, b"not a pdf", "text/plain"))


@pytest.mark.asyncio
async def test_upload_documento(client: AsyncClient):
    response = await client.post(
        "/api/v1/documenti/",
        files=[pdf_file()],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["mime_type"] == "application/pdf"
    assert "checksum" in data
    assert data["tipo_documento_codice"] is None


@pytest.mark.asyncio
async def test_upload_documento_con_tipo(client: AsyncClient):
    response = await client.post(
        "/api/v1/documenti/?tipo_documento_codice=3",
        files=[pdf_file()],
    )
    assert response.status_code == 201
    assert response.json()["tipo_documento_codice"] == 3


@pytest.mark.asyncio
async def test_upload_documento_non_pdf_now_accepted(client: AsyncClient):
    # All file types are now accepted; the PDF-only restriction has been removed.
    response = await client.post(
        "/api/v1/documenti/",
        files=[fake_file()],
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_documento_not_found(client: AsyncClient):
    response = await client.get("/api/v1/documenti/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_documenti_empty(client: AsyncClient):
    response = await client.get("/api/v1/documenti/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0
    assert data["meta"]["page"] == 1


@pytest.mark.asyncio
async def test_list_documenti_filtro_tipo(client: AsyncClient):
    await client.post(
        "/api/v1/documenti/?tipo_documento_codice=1", files=[pdf_file("a.pdf")]
    )
    await client.post(
        "/api/v1/documenti/?tipo_documento_codice=3", files=[pdf_file("b.pdf")]
    )
    response = await client.get("/api/v1/documenti/?tipo_documento_codice=1")
    assert response.json()["meta"]["total_items"] == 1


@pytest.mark.asyncio
async def test_delete_documento(client: AsyncClient):
    upload = await client.post("/api/v1/documenti/", files=[pdf_file("del.pdf")])
    doc_id = upload.json()["id"]
    response = await client.delete(f"/api/v1/documenti/{doc_id}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/documenti/{doc_id}")).status_code == 404


@pytest.mark.asyncio
async def test_download_documento(client: AsyncClient):
    upload = await client.post(
        "/api/v1/documenti/", files=[pdf_file("scaricabile.pdf")]
    )
    doc_id = upload.json()["id"]
    response = await client.get(f"/api/v1/documenti/{doc_id}/download")
    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 test pdf content"


@pytest.mark.asyncio
async def test_preview_documento_inline(client: AsyncClient):
    upload = await client.post("/api/v1/documenti/", files=[pdf_file("anteprima.pdf")])
    doc_id = upload.json()["id"]
    response = await client.get(f"/api/v1/documenti/{doc_id}/preview")
    assert response.status_code == 200
    assert response.headers["content-disposition"].lower().startswith("inline")


@pytest.mark.asyncio
async def test_preview_documento_not_found(client: AsyncClient):
    response = await client.get("/api/v1/documenti/999/preview")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_documento_missing_file(client: AsyncClient):
    upload = await client.post("/api/v1/documenti/", files=[pdf_file("fantasma.pdf")])
    data = upload.json()
    os.remove(data["file_path"])
    response = await client.get(f"/api/v1/documenti/{data['id']}/download")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Helpers and fixtures for sotto-cartella RBAC tests
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


@pytest.fixture
async def seeded_sotto_cartella(
    seeded_macro_sezioni: None, db_session: AsyncSession
) -> int:
    """Seed one SottoCartella under macro-sezione 1 (certificazioni).

    Returns the row ID so tests can pass it as sotto_cartella_id query param.
    """
    sc = SottoCartella(nome="Cartella Test", macro_sezione_codice=1)
    db_session.add(sc)
    await db_session.commit()
    await db_session.refresh(sc)
    return sc.id


# ---------------------------------------------------------------------------
# New RBAC tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_documento_with_sotto_cartella_requires_write_permission(
    client: AsyncClient, seeded_sotto_cartella: int
) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"archivio:read"}
    )
    r = await client.post(
        f"/api/v1/documenti/?sotto_cartella_id={seeded_sotto_cartella}",
        files=[pdf_file("rbac_upload.pdf")],
    )
    assert r.status_code == 403
    assert "certificazioni:write" in r.json()["detail"]


@pytest.mark.asyncio
async def test_upload_documento_with_sotto_cartella_succeeds_with_permission(
    client: AsyncClient, seeded_sotto_cartella: int
) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"certificazioni:write"}
    )
    r = await client.post(
        f"/api/v1/documenti/?sotto_cartella_id={seeded_sotto_cartella}",
        files=[pdf_file("upload_ok.pdf")],
    )
    assert r.status_code == 201
    data = r.json()
    assert data["sotto_cartella_id"] == seeded_sotto_cartella
    assert data["sotto_cartella"]["nome"] == "Cartella Test"


@pytest.mark.asyncio
async def test_upload_documento_without_sotto_cartella_still_works_ungated(
    client: AsyncClient,
) -> None:
    # Regression guard: a user with no archivio permissions can still upload
    # a document that has no sotto_cartella_id (pre-CR behavior preserved).
    app.dependency_overrides[get_current_user] = lambda: _user(permessi=set())
    r = await client.post("/api/v1/documenti/", files=[pdf_file("ungated.pdf")])
    assert r.status_code == 201
    assert r.json()["sotto_cartella_id"] is None


@pytest.mark.asyncio
async def test_list_documenti_filtered_by_sotto_cartella_requires_read_permission(
    client: AsyncClient, seeded_sotto_cartella: int
) -> None:
    # write but NOT read
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"certificazioni:write"}
    )
    url = f"/api/v1/documenti/?sotto_cartella_id={seeded_sotto_cartella}"
    r = await client.get(url)
    assert r.status_code == 403
    assert "certificazioni:read" in r.json()["detail"]


@pytest.mark.asyncio
async def test_list_documenti_filtered_by_sotto_cartella_succeeds_with_permission(
    client: AsyncClient, seeded_sotto_cartella: int
) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"certificazioni:read"}
    )
    url = f"/api/v1/documenti/?sotto_cartella_id={seeded_sotto_cartella}"
    r = await client.get(url)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert data["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_list_documenti_without_sotto_cartella_filter_still_ungated(
    client: AsyncClient,
) -> None:
    # Regression guard: listing without a sotto_cartella_id filter requires no
    # specific archivio permission (pre-CR behavior preserved).
    app.dependency_overrides[get_current_user] = lambda: _user(permessi=set())
    r = await client.get("/api/v1/documenti/")
    assert r.status_code == 200
    assert r.json()["items"] == []


@pytest.mark.asyncio
async def test_delete_documento_in_sotto_cartella_requires_write_permission(
    client: AsyncClient, seeded_sotto_cartella: int
) -> None:
    # Upload as superuser (default override), then switch to unpermissioned user.
    upload = await client.post(
        f"/api/v1/documenti/?sotto_cartella_id={seeded_sotto_cartella}",
        files=[pdf_file("da_eliminare.pdf")],
    )
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"archivio:read"}
    )
    r = await client.delete(f"/api/v1/documenti/{doc_id}")
    assert r.status_code == 403
    assert "certificazioni:write" in r.json()["detail"]


@pytest.mark.asyncio
async def test_upload_documento_unknown_sotto_cartella_404(
    client: AsyncClient,
) -> None:
    r = await client.post(
        "/api/v1/documenti/?sotto_cartella_id=99999",
        files=[pdf_file("orphan.pdf")],
    )
    assert r.status_code == 404
