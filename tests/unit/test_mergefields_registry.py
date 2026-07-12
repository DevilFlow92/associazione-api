from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.mergefields.providers.banda_provider import BandaProvider
from app.mergefields.providers.contatto_provider import ContattoProvider
from app.mergefields.providers.esterno_provider import EsternoProvider
from app.mergefields.providers.iscrizione_provider import IscrizioneProvider
from app.mergefields.providers.ricevuta_provider import RicevutaProvider
from app.mergefields.providers.servizio_provider import ServizioProvider
from app.mergefields.providers.socio_provider import SocioProvider
from app.mergefields.registry import REGISTRY, list_all_fields, resolve_context


async def _create_persona(
    ac: AsyncClient,
    *,
    nome: str = "Mario",
    cognome: str = "Rossi",
    codice_fiscale: str = "RSSMRA80A01H501U",
    data_nascita: str = "1980-01-01",
    ragione_sociale: str | None = None,
    comune_nascita_codice: int | None = None,
) -> dict:
    resp = await ac.post(
        "/api/v1/persone/",
        json={
            "banda_codice": 1,
            "nome": nome,
            "cognome": cognome,
            "codice_fiscale": codice_fiscale,
            "data_nascita": data_nascita,
            "ragione_sociale": ragione_sociale,
            "comune_nascita_codice": comune_nascita_codice,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_comune(
    ac: AsyncClient, *, codice: int = 1, descrizione: str = "Cagliari"
) -> dict:
    resp = await ac.post(
        "/api/v1/comuni/", json={"codice": codice, "descrizione": descrizione}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_ruolo_contatto(
    ac: AsyncClient, *, codice: int = 1, descrizione: str = "Referente"
) -> dict:
    resp = await ac.post(
        "/api/v1/ruoli-contatto/", json={"codice": codice, "descrizione": descrizione}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_stato_iscrizione(
    ac: AsyncClient, *, codice: int = 1, descrizione: str = "Pagata"
) -> dict:
    resp = await ac.post(
        "/api/v1/stati-iscrizione/", json={"codice": codice, "descrizione": descrizione}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_ruolo_banda(
    ac: AsyncClient, *, codice: int = 10, descrizione: str = "Socio Bandista"
) -> dict:
    resp = await ac.post(
        "/api/v1/ruoli-banda/", json={"codice": codice, "descrizione": descrizione}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_strumento(
    ac: AsyncClient, *, codice: int = 1, descrizione: str = "Flauto"
) -> dict:
    resp = await ac.post(
        "/api/v1/strumenti/", json={"codice": codice, "descrizione": descrizione}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_socio(
    ac: AsyncClient,
    persona_id: int,
    codice: str = "S001",
    *,
    strumento_codice: int | None = None,
) -> dict:
    resp = await ac.post(
        "/api/v1/soci/",
        json={
            "persona_id": persona_id,
            "codice_socio": codice,
            "ruolo_banda_codice": 10,
            "strumento_codice": strumento_codice,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_servizio(ac: AsyncClient) -> dict:
    indirizzo = await _create_indirizzo(ac)
    resp = await ac.post(
        "/api/v1/servizi/",
        json={
            "banda_codice": 1,
            "anno": 2026,
            "descrizione_servizio": "Concerto estivo",
            "data_servizio": "2026-07-20T21:00:00",
            "indirizzo_id": indirizzo["id"],
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
    assert set(REGISTRY) == {
        "socio",
        "esterno",
        "banda",
        "contatto",
        "iscrizione",
        "servizio",
        "ricevuta",
    }
    assert isinstance(REGISTRY["socio"], SocioProvider)
    assert isinstance(REGISTRY["esterno"], EsternoProvider)
    assert isinstance(REGISTRY["banda"], BandaProvider)
    assert isinstance(REGISTRY["contatto"], ContattoProvider)
    assert isinstance(REGISTRY["iscrizione"], IscrizioneProvider)
    assert isinstance(REGISTRY["servizio"], ServizioProvider)
    assert isinstance(REGISTRY["ricevuta"], RicevutaProvider)


def test_list_all_fields_grouped_by_entity():
    fields = list_all_fields()
    assert set(fields) == {
        "socio",
        "esterno",
        "banda",
        "contatto",
        "iscrizione",
        "servizio",
        "ricevuta",
    }
    socio_keys = {f.chiave for f in fields["socio"]}
    assert {"codice_socio", "nome", "cognome", "codice_fiscale", "data_nascita"} <= (
        socio_keys
    )


@pytest.mark.asyncio
async def test_socio_provider_resolve(client: AsyncClient, db_session: AsyncSession):
    await _create_ruolo_banda(client, codice=10, descrizione="Socio Bandista")
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
    assert result["ragione_sociale"] is None
    assert result["luogo_nascita"] is None
    assert result["ruolo_banda"] == "Socio Bandista"
    assert result["strumento"] is None


@pytest.mark.asyncio
async def test_socio_provider_resolve_ragione_sociale_e_luogo_nascita(
    client: AsyncClient, db_session: AsyncSession
):
    await _create_ruolo_banda(client, codice=10, descrizione="Socio Bandista")
    await _create_strumento(client, codice=1, descrizione="Flauto")
    comune = await _create_comune(client, codice=1, descrizione="Cagliari")
    persona = await _create_persona(
        client,
        ragione_sociale="Associazione XYZ",
        comune_nascita_codice=comune["codice"],
    )
    socio = await _create_socio(client, persona["id"], strumento_codice=1)

    result = await SocioProvider().resolve(socio["id"], db_session)
    assert result["ragione_sociale"] == "Associazione XYZ"
    assert result["luogo_nascita"] == "Cagliari"
    assert result["ruolo_banda"] == "Socio Bandista"
    assert result["strumento"] == "Flauto"


@pytest.mark.asyncio
async def test_esterno_provider_resolve(client: AsyncClient, db_session: AsyncSession):
    await _create_strumento(client, codice=1, descrizione="Flauto")
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
    assert result["ragione_sociale"] is None
    assert result["luogo_nascita"] is None
    assert result["strumento"] == "Flauto"


@pytest.mark.asyncio
async def test_esterno_provider_resolve_ragione_sociale_e_luogo_nascita(
    client: AsyncClient, db_session: AsyncSession
):
    await _create_strumento(client, codice=1, descrizione="Flauto")
    comune = await _create_comune(client, codice=1, descrizione="Sassari")
    persona = await _create_persona(
        client,
        nome="Luigi",
        cognome="Verdi",
        ragione_sociale="Ditta ABC",
        comune_nascita_codice=comune["codice"],
    )
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
    assert result["ragione_sociale"] == "Ditta ABC"
    assert result["luogo_nascita"] == "Sassari"


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
    await _create_ruolo_banda(client, codice=10, descrizione="Socio Bandista")
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


@pytest.mark.asyncio
async def test_contatto_provider_resolve(client: AsyncClient, db_session: AsyncSession):
    await _create_ruolo_contatto(client, codice=1, descrizione="Referente")
    persona = await _create_persona(client)

    contatto_resp = await client.post(
        "/api/v1/contatti/",
        json={
            "persona_id": persona["id"],
            "ruolo_contatto_codice": 1,
            "email": "mario.rossi@test.com",
            "telefono": "070123456",
        },
    )
    assert contatto_resp.status_code == 201, contatto_resp.text
    contatto_id = contatto_resp.json()["id"]

    result = await ContattoProvider().resolve(contatto_id, db_session)
    assert result["email"] == "mario.rossi@test.com"
    assert result["telefono"] == "070123456"
    assert result["ruolo_contatto"] == "Referente"


@pytest.mark.asyncio
async def test_iscrizione_provider_resolve(
    client: AsyncClient, db_session: AsyncSession
):
    await _create_stato_iscrizione(client, codice=1, descrizione="In attesa")
    persona = await _create_persona(client)
    socio = await _create_socio(client, persona["id"])

    iscrizione_resp = await client.post(
        "/api/v1/iscrizioni/",
        json={
            "socio_id": socio["id"],
            "anno": 2026,
            "quota_partecipazione": 15.0,
            "stato_iscrizione_codice": 1,
            "data_iscrizione": "2026-01-10",
            "note": "Iscrizione anticipata",
        },
    )
    assert iscrizione_resp.status_code == 201, iscrizione_resp.text
    iscrizione_id = iscrizione_resp.json()["id"]

    result = await IscrizioneProvider().resolve(iscrizione_id, db_session)
    assert result["anno"] == 2026
    assert result["quota_partecipazione"] == "€ 15,00"
    assert result["stato_iscrizione"] == "In attesa"
    assert str(result["data_iscrizione"]) == "2026-01-10"
    assert result["note"] == "Iscrizione anticipata"


@pytest.mark.asyncio
async def test_servizio_provider_resolve(client: AsyncClient, db_session: AsyncSession):
    servizio = await _create_servizio(client)

    result = await ServizioProvider().resolve(servizio["id"], db_session)
    assert result["descrizione_servizio"] == "Concerto estivo"
    assert str(result["data_servizio"]) == "2026-07-20 21:00:00"
    assert result["indirizzo_completo"] == "Via Roma, 1, 00100"
    assert result["anno"] == 2026
    assert result["note"] is None


@pytest.mark.asyncio
async def test_ricevuta_provider_resolve(client: AsyncClient, db_session: AsyncSession):
    servizio = await _create_servizio(client)

    ricevuta_resp = await client.post(
        "/api/v1/ricevute/",
        json={
            "servizio_id": servizio["id"],
            "data_ricevuta": "2026-07-21T10:00:00",
            "importo": 150.50,
            "note_in_stampa": "Compenso servizio",
            "note_fuori_stampa": "Pagamento in contanti",
        },
    )
    assert ricevuta_resp.status_code == 201, ricevuta_resp.text
    ricevuta_id = ricevuta_resp.json()["id"]

    result = await RicevutaProvider().resolve(ricevuta_id, db_session)
    assert str(result["data_ricevuta"]) == "2026-07-21 10:00:00"
    assert result["importo"] == "€ 150,50"
    assert result["note_in_stampa"] == "Compenso servizio"
    assert result["note_fuori_stampa"] == "Pagamento in contanti"
