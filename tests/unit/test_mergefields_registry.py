from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.mergefields.providers.banda_provider import BandaProvider
from app.mergefields.providers.esterno_provider import EsternoProvider
from app.mergefields.providers.socio_provider import SocioProvider
from app.mergefields.registry import REGISTRY, list_all_fields, resolve_context


async def _create_persona(
    ac: AsyncClient,
    *,
    nome: str = "Mario",
    cognome: str = "Rossi",
    codice_fiscale: str = "RSSMRA80A01H501U",
    data_nascita: str = "1980-01-01",
) -> dict:
    resp = await ac.post(
        "/api/v1/persone/",
        json={
            "banda_codice": 1,
            "nome": nome,
            "cognome": cognome,
            "codice_fiscale": codice_fiscale,
            "data_nascita": data_nascita,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_indirizzo(ac: AsyncClient) -> dict:
    resp = await ac.post(
        "/api/v1/indirizzi/",
        json={
            "tipo_indirizzo_codice": 2,
            "prima_riga": "Via Roma",
            "numero_civico": "1",
            "cap": "00100",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_registry_contains_expected_providers():
    assert set(REGISTRY) == {"socio", "esterno", "banda"}
    assert isinstance(REGISTRY["socio"], SocioProvider)
    assert isinstance(REGISTRY["esterno"], EsternoProvider)
    assert isinstance(REGISTRY["banda"], BandaProvider)


def test_list_all_fields_grouped_by_entity():
    fields = list_all_fields()
    assert set(fields) == {"socio", "esterno", "banda"}
    socio_keys = {f.chiave for f in fields["socio"]}
    assert {"codice_socio", "nome", "cognome", "codice_fiscale", "data_nascita"} <= (
        socio_keys
    )


@pytest.mark.asyncio
async def test_socio_provider_resolve(client: AsyncClient, db_session: AsyncSession):
    persona = await _create_persona(client)
    indirizzo = await _create_indirizzo(client)
    await client.put(f"/api/v1/persone/{persona['id']}/indirizzi/{indirizzo['id']}")

    socio_resp = await client.post(
        "/api/v1/soci/",
        json={
            "persona_id": persona["id"],
            "codice_socio": "S001",
            "ruolo_banda_codice": 10,
        },
    )
    assert socio_resp.status_code == 201, socio_resp.text
    socio_id = socio_resp.json()["id"]

    result = await SocioProvider().resolve(socio_id, db_session)
    assert result["codice_socio"] == "S001"
    assert result["nome"] == "Mario"
    assert result["cognome"] == "Rossi"
    assert result["codice_fiscale"] == "RSSMRA80A01H501U"
    assert result["indirizzo_completo"] == "Via Roma, 1, 00100"


@pytest.mark.asyncio
async def test_esterno_provider_resolve(client: AsyncClient, db_session: AsyncSession):
    persona = await _create_persona(client, nome="Luigi", cognome="Verdi")

    esterno_resp = await client.post(
        "/api/v1/esterni/",
        json={
            "persona_id": persona["id"],
            "codice_esterno": "E001",
            "strumento_codice": 1,
        },
    )
    assert esterno_resp.status_code == 201, esterno_resp.text
    esterno_id = esterno_resp.json()["id"]

    result = await EsternoProvider().resolve(esterno_id, db_session)
    assert result["codice_esterno"] == "E001"
    assert result["nome"] == "Luigi"
    assert result["cognome"] == "Verdi"
    assert result["indirizzo_completo"] is None


@pytest.mark.asyncio
async def test_banda_provider_resolve(client: AsyncClient, db_session: AsyncSession):
    banda_resp = await client.post(
        "/api/v1/bande/", json={"codice": 1, "descrizione": "Banda di Test"}
    )
    assert banda_resp.status_code == 201, banda_resp.text

    result = await BandaProvider().resolve(1, db_session)
    assert result["descrizione"] == "Banda di Test"
    assert result["indirizzo_completo"] is None


@pytest.mark.asyncio
async def test_resolve_context_groups_by_entity(
    client: AsyncClient, db_session: AsyncSession
):
    persona = await _create_persona(client)
    socio_resp = await client.post(
        "/api/v1/soci/",
        json={
            "persona_id": persona["id"],
            "codice_socio": "S001",
            "ruolo_banda_codice": 10,
        },
    )
    socio_id = socio_resp.json()["id"]
    await client.post(
        "/api/v1/bande/", json={"codice": 1, "descrizione": "Banda di Test"}
    )

    context = await resolve_context({"socio": socio_id, "banda": 1}, db_session)
    assert context["socio"]["codice_socio"] == "S001"
    assert context["banda"]["descrizione"] == "Banda di Test"
