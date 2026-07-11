from __future__ import annotations

from httpx import AsyncClient

from app.api.deps import get_current_user
from app.models.utente import TipoUtente, Utente
from main import app


async def test_list_mergefields(client: AsyncClient):
    resp = await client.get("/api/v1/mergefields/")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["entita"]) == {
        "socio",
        "esterno",
        "banda",
        "contatto",
        "iscrizione",
        "servizio",
        "ricevuta",
    }

    socio_fields = {f["chiave"]: f["tipo"] for f in data["entita"]["socio"]}
    assert socio_fields["codice_socio"] == "str"
    assert socio_fields["data_nascita"] == "date"


async def test_list_mergefields_forbidden_without_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: Utente(
        id=1, tipo=TipoUtente.UMANO, email="test@example.com", superuser=False
    )
    resp = await client.get("/api/v1/mergefields/")
    assert resp.status_code == 403


async def test_list_mergefields_requires_authentication(client: AsyncClient):
    app.dependency_overrides.pop(get_current_user, None)
    resp = await client.get("/api/v1/mergefields/")
    assert resp.status_code == 401
