"""Percorso formativo pluriennale di una persona (card #220): endpoint di
sola lettura che aggrega le sue iscrizioni a corsi nel tempo con il
riepilogo delle voci di ciascuna scheda alunno.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user
from main import app
from tests.unit.test_schede_alunno import (
    _user,
    create_categoria_voce,
    create_corso,
    create_iscrizione_corso,
    create_persona,
    create_scheda,
    create_stato,
    create_voce_catalogo,
    create_voce_scheda,
)


@pytest.mark.asyncio
async def test_percorso_formativo_ordinato_per_anno_decrescente_con_riepilogo(
    client: AsyncClient,
):
    persona = await create_persona(client)
    stato = await create_stato(client)

    corso_2024 = await create_corso(client, tipo_corso_codice=1, anno=2024)
    corso_2026 = await create_corso(client, tipo_corso_codice=2, anno=2026)

    iscrizione_2024 = await create_iscrizione_corso(
        client, corso_2024["id"], persona["id"], stato["codice"]
    )
    iscrizione_2026 = await create_iscrizione_corso(
        client, corso_2026["id"], persona["id"], stato["codice"]
    )

    scheda_2024 = await create_scheda(client, iscrizione_2024["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo_1 = await create_voce_catalogo(client, 1, categoria["codice"])
    voce_catalogo_2 = await create_voce_catalogo(
        client, 1, categoria["codice"], testo="Scala di Re maggiore"
    )
    voce = await create_voce_scheda(
        client, scheda_2024["id"], voce_catalogo_1["id"], stato="da_iniziare"
    )
    await client.patch(
        f"/api/v1/schede-alunno/{scheda_2024['id']}/voci/{voce['id']}",
        json={"stato": "acquisita"},
    )
    await create_voce_scheda(
        client, scheda_2024["id"], voce_catalogo_2["id"], stato="in_corso", ordine=2
    )

    scheda_2026 = await create_scheda(client, iscrizione_2026["id"])

    response = await client.get(f"/api/v1/persone/{persona['id']}/percorso-formativo")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["iscrizione_corso_id"] == iscrizione_2026["id"]
    assert data[0]["corso"]["anno"] == 2026
    assert data[0]["scheda_alunno_id"] == scheda_2026["id"]
    assert data[0]["riepilogo_voci"] == {
        "totale": 0,
        "da_iniziare": 0,
        "in_corso": 0,
        "acquisita": 0,
    }

    assert data[1]["iscrizione_corso_id"] == iscrizione_2024["id"]
    assert data[1]["corso"]["anno"] == 2024
    assert data[1]["scheda_alunno_id"] == scheda_2024["id"]
    assert data[1]["riepilogo_voci"] == {
        "totale": 2,
        "da_iniziare": 0,
        "in_corso": 1,
        "acquisita": 1,
    }


@pytest.mark.asyncio
async def test_percorso_formativo_iscrizione_senza_scheda_inclusa(client: AsyncClient):
    persona = await create_persona(client)
    stato = await create_stato(client)
    corso = await create_corso(client)
    iscrizione = await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato["codice"]
    )

    response = await client.get(f"/api/v1/persone/{persona['id']}/percorso-formativo")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["iscrizione_corso_id"] == iscrizione["id"]
    assert data[0]["scheda_alunno_id"] is None
    assert data[0]["riepilogo_voci"] == {
        "totale": 0,
        "da_iniziare": 0,
        "in_corso": 0,
        "acquisita": 0,
    }


@pytest.mark.asyncio
async def test_percorso_formativo_persona_senza_iscrizioni_lista_vuota(
    client: AsyncClient,
):
    persona = await create_persona(client)

    response = await client.get(f"/api/v1/persone/{persona['id']}/percorso-formativo")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_percorso_formativo_persona_inesistente_404(client: AsyncClient):
    response = await client.get("/api/v1/persone/999/percorso-formativo")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_percorso_formativo_ok_con_corsi_read(client: AsyncClient):
    persona = await create_persona(client)

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    try:
        response = await client.get(
            f"/api/v1/persone/{persona['id']}/percorso-formativo"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_percorso_formativo_forbidden_senza_corsi_read(client: AsyncClient):
    persona = await create_persona(client)

    app.dependency_overrides[get_current_user] = lambda: _user()
    try:
        response = await client.get(
            f"/api/v1/persone/{persona['id']}/percorso-formativo"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
