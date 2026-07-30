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


BASE = "/api/v1/pagamenti-corso"
CFG_BASE = "/api/v1/configurazioni-banda-anno"


async def create_tipo_corso(
    client: AsyncClient, codice: int = 1, descrizione: str = "Ottoni"
) -> dict:
    response = await client.post(
        "/api/v1/tipi-corso/", json={"codice": codice, "descrizione": descrizione}
    )
    assert response.status_code == 201
    return response.json()


async def create_corso(
    client: AsyncClient, tipo_corso_codice: int = 1, **overrides
) -> dict:
    tipo = await create_tipo_corso(client, codice=tipo_corso_codice)
    payload = {"banda_codice": 1, "tipo_corso_codice": tipo["codice"], "anno": 2026}
    payload.update(overrides)
    response = await client.post("/api/v1/corsi/", json=payload)
    assert response.status_code == 201
    return response.json()


async def create_persona(
    client: AsyncClient, nome: str = "Mario", cognome: str = "Rossi"
) -> dict:
    response = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": 1, "nome": nome, "cognome": cognome},
    )
    assert response.status_code == 201
    return response.json()


async def create_stato(
    client: AsyncClient, codice: int = 1, descrizione: str = "Confermata"
) -> dict:
    response = await client.post(
        "/api/v1/stati-iscrizione-corso/",
        json={"codice": codice, "descrizione": descrizione},
    )
    assert response.status_code == 201
    return response.json()


async def create_iscrizione_corso(
    client: AsyncClient, corso_id: int, persona_id: int, stato_codice: int, **overrides
) -> dict:
    payload = {
        "corso_id": corso_id,
        "persona_id": persona_id,
        "stato_iscrizione_corso_codice": stato_codice,
        "data_iscrizione": "2026-09-01",
    }
    payload.update(overrides)
    response = await client.post("/api/v1/iscrizioni-corso/", json=payload)
    assert response.status_code == 201
    return response.json()


async def get_or_create_stato(
    client: AsyncClient, codice: int = 1, descrizione: str = "Confermata"
) -> dict:
    """Come create_stato, ma riusa lo stato se già creato in questo test
    (setup_iscrizione_corso può essere invocato più volte nello stesso test)."""
    response = await client.post(
        "/api/v1/stati-iscrizione-corso/",
        json={"codice": codice, "descrizione": descrizione},
    )
    if response.status_code == 409:
        get_resp = await client.get(f"/api/v1/stati-iscrizione-corso/{codice}")
        assert get_resp.status_code == 200
        return get_resp.json()
    assert response.status_code == 201
    return response.json()


async def setup_iscrizione_corso(client: AsyncClient, **corso_overrides) -> dict:
    """Crea corso + persona + stato + iscrizione_corso, ritorna l'iscrizione."""
    corso = await create_corso(client, **corso_overrides)
    persona = await create_persona(client)
    stato = await get_or_create_stato(client)
    return await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato["codice"]
    )


async def create_voce_rette_corsi(client: AsyncClient, banda_codice: int = 1) -> dict:
    response = await client.post(
        "/api/v1/voci-contabilita/",
        json={
            "banda_codice": banda_codice,
            "voce_contabilita": "Rette corsi",
            "sezione_rendiconto_codice": 2,  # Entrate
            "voce_rendiconto_codice": 2,  # A) Entrate da attività di interesse generale
            "sottovoce_rendiconto_codice": 8,  # 3) Entrate per prestazioni/cessioni
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def setup_pagamento_env(client: AsyncClient, anno: int = 2026) -> dict:
    """Seed NaturaFlusso 'Banca' + ConfigurazioneBandaAnno con
    voce_contabilita_corsi_id impostato. Ritorna la cfg."""
    await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Banca"}
    )
    cfg_resp = await client.post(f"{CFG_BASE}/", json={"banda_codice": 1, "anno": anno})
    assert cfg_resp.status_code == 201, cfg_resp.text
    cfg = cfg_resp.json()

    voce_rette = await create_voce_rette_corsi(client)

    patch_resp = await client.patch(
        f"{CFG_BASE}/{cfg['id']}",
        json={"voce_contabilita_corsi_id": voce_rette["id"]},
    )
    assert patch_resp.status_code == 200, patch_resp.text
    return patch_resp.json()


def pagamento_payload(iscrizione_corso_id: int, **overrides) -> dict:
    payload = {
        "iscrizione_corso_id": iscrizione_corso_id,
        "data_pagamento": "2026-02-10",
        "importo": 50.0,
    }
    payload.update(overrides)
    return payload


async def create_pagamento(
    client: AsyncClient, iscrizione_corso_id: int, **overrides
) -> dict:
    response = await client.post(
        f"{BASE}/", json=pagamento_payload(iscrizione_corso_id, **overrides)
    )
    assert response.status_code == 201, response.text
    return response.json()


async def get_auto_flussi_corso(client: AsyncClient) -> list[dict]:
    resp = await client.get("/api/v1/flussi-cassa/")
    assert resp.status_code == 200
    return [f for f in resp.json()["items"] if f["tipo"] == "AUTO_PAGAMENTO_CORSO"]


# ── Auto-posting: creazione ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_pagamento_crea_ricevuta_e_flusso(client: AsyncClient):
    await setup_pagamento_env(client)
    iscrizione = await setup_iscrizione_corso(client)

    response = await client.post(
        f"{BASE}/",
        json=pagamento_payload(
            iscrizione["id"], importo=75.0, data_pagamento="2026-03-01"
        ),
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["iscrizione_corso_id"] == iscrizione["id"]
    assert float(data["importo"]) == 75.0
    assert data["ricevuta_id"] is not None
    assert data["ricevuta"]["importo"] == 75.0
    assert data["ricevuta"]["tipo_ricevuta"] == "RISCOSSIONE"
    assert data["ricevuta"]["persona_id"] == iscrizione["persona_id"]

    # Verifica diretta della Ricevuta creata
    ricevuta_resp = await client.get(f"/api/v1/ricevute/{data['ricevuta_id']}")
    assert ricevuta_resp.status_code == 200
    ricevuta = ricevuta_resp.json()
    assert ricevuta["tipo_ricevuta"] == "RISCOSSIONE"
    assert ricevuta["persona_id"] == iscrizione["persona_id"]
    assert ricevuta["importo"] == 75.0

    # Verifica del FlussoCassa AUTO_PAGAMENTO_CORSO
    flussi = await get_auto_flussi_corso(client)
    assert len(flussi) == 1
    flusso = flussi[0]
    assert flusso["pagamento_corso_id"] == data["id"]
    assert float(flusso["importo"]) == 75.0
    assert flusso["segno"] == "+"
    assert "2026-03-01" in flusso["data_registrazione"]
    assert "Mario" in flusso["descrizione_operazione"]
    assert "Rossi" in flusso["descrizione_operazione"]


@pytest.mark.asyncio
async def test_create_pagamento_iscrizione_corso_not_found(client: AsyncClient):
    await setup_pagamento_env(client)
    response = await client.post(f"{BASE}/", json=pagamento_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_pagamento_senza_voce_corsi_422(client: AsyncClient):
    await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Banca"}
    )
    cfg_resp = await client.post(f"{CFG_BASE}/", json={"banda_codice": 1, "anno": 2026})
    assert cfg_resp.status_code == 201
    assert cfg_resp.json()["voce_contabilita_corsi"] is None

    iscrizione = await setup_iscrizione_corso(client)
    response = await client.post(f"{BASE}/", json=pagamento_payload(iscrizione["id"]))
    assert response.status_code == 422

    # Nessuna riga deve essere stata persistita
    assert (await client.get(f"{BASE}/")).json()["meta"]["total_items"] == 0
    assert (await client.get("/api/v1/ricevute/")).json()["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_create_pagamento_senza_configurazione_422(client: AsyncClient):
    await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Banca"}
    )
    # Nessuna ConfigurazioneBandaAnno creata affatto
    iscrizione = await setup_iscrizione_corso(client)
    response = await client.post(f"{BASE}/", json=pagamento_payload(iscrizione["id"]))
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_pagamento_anno_chiuso_409(client: AsyncClient):
    cfg = await setup_pagamento_env(client)
    close_resp = await client.post(f"{CFG_BASE}/{cfg['id']}/chiudi")
    assert close_resp.status_code == 200

    iscrizione = await setup_iscrizione_corso(client)
    response = await client.post(f"{BASE}/", json=pagamento_payload(iscrizione["id"]))
    assert response.status_code == 409

    assert (await client.get(f"{BASE}/")).json()["meta"]["total_items"] == 0


# ── CRUD base ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_pagamento_not_found(client: AsyncClient):
    response = await client.get(f"{BASE}/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_pagamenti_filtro_iscrizione_corso(client: AsyncClient):
    await setup_pagamento_env(client)
    iscrizione1 = await setup_iscrizione_corso(client, tipo_corso_codice=1)
    iscrizione2 = await setup_iscrizione_corso(client, tipo_corso_codice=2)

    await create_pagamento(client, iscrizione1["id"])
    await create_pagamento(client, iscrizione1["id"], data_pagamento="2026-04-01")
    await create_pagamento(client, iscrizione2["id"])

    response = await client.get(
        f"{BASE}/", params={"iscrizione_corso_id": iscrizione1["id"]}
    )
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 2


# ── Update: propagazione a Ricevuta + FlussoCassa ────────────────────────────


@pytest.mark.asyncio
async def test_update_importo_propaga_a_ricevuta_e_flusso(client: AsyncClient):
    await setup_pagamento_env(client)
    iscrizione = await setup_iscrizione_corso(client)
    pagamento = await create_pagamento(client, iscrizione["id"], importo=50.0)

    response = await client.patch(f"{BASE}/{pagamento['id']}", json={"importo": 120.0})
    assert response.status_code == 200
    assert float(response.json()["importo"]) == 120.0

    ricevuta_resp = await client.get(f"/api/v1/ricevute/{pagamento['ricevuta_id']}")
    assert ricevuta_resp.json()["importo"] == 120.0

    flussi = await get_auto_flussi_corso(client)
    assert len(flussi) == 1
    assert float(flussi[0]["importo"]) == 120.0


@pytest.mark.asyncio
async def test_update_data_pagamento_propaga_a_ricevuta_e_flusso(client: AsyncClient):
    await setup_pagamento_env(client)
    iscrizione = await setup_iscrizione_corso(client)
    pagamento = await create_pagamento(client, iscrizione["id"])

    response = await client.patch(
        f"{BASE}/{pagamento['id']}", json={"data_pagamento": "2026-05-20"}
    )
    assert response.status_code == 200
    assert response.json()["data_pagamento"] == "2026-05-20"

    ricevuta_resp = await client.get(f"/api/v1/ricevute/{pagamento['ricevuta_id']}")
    assert "2026-05-20" in ricevuta_resp.json()["data_ricevuta"]

    flussi = await get_auto_flussi_corso(client)
    assert "2026-05-20" in flussi[0]["data_registrazione"]


@pytest.mark.asyncio
async def test_update_note_non_tocca_ricevuta_e_flusso(client: AsyncClient):
    await setup_pagamento_env(client)
    iscrizione = await setup_iscrizione_corso(client)
    pagamento = await create_pagamento(client, iscrizione["id"], importo=50.0)

    response = await client.patch(
        f"{BASE}/{pagamento['id']}", json={"note": "Pagato in contanti"}
    )
    assert response.status_code == 200
    assert response.json()["note"] == "Pagato in contanti"

    ricevuta_resp = await client.get(f"/api/v1/ricevute/{pagamento['ricevuta_id']}")
    assert ricevuta_resp.json()["importo"] == 50.0
    flussi = await get_auto_flussi_corso(client)
    assert float(flussi[0]["importo"]) == 50.0


@pytest.mark.asyncio
async def test_update_pagamento_not_found(client: AsyncClient):
    response = await client.patch(f"{BASE}/999", json={"importo": 10.0})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_pagamento_anno_chiuso_409(client: AsyncClient):
    cfg = await setup_pagamento_env(client)
    iscrizione = await setup_iscrizione_corso(client)
    pagamento = await create_pagamento(client, iscrizione["id"])

    close_resp = await client.post(f"{CFG_BASE}/{cfg['id']}/chiudi")
    assert close_resp.status_code == 200

    response = await client.patch(f"{BASE}/{pagamento['id']}", json={"importo": 99.0})
    assert response.status_code == 409


# ── Delete: cascata su FlussoCassa e Ricevuta ────────────────────────────────


@pytest.mark.asyncio
async def test_delete_pagamento_elimina_flusso_e_ricevuta(client: AsyncClient):
    await setup_pagamento_env(client)
    iscrizione = await setup_iscrizione_corso(client)
    pagamento = await create_pagamento(client, iscrizione["id"])
    ricevuta_id = pagamento["ricevuta_id"]
    assert len(await get_auto_flussi_corso(client)) == 1

    response = await client.delete(f"{BASE}/{pagamento['id']}")
    assert response.status_code == 204

    assert (await client.get(f"{BASE}/{pagamento['id']}")).status_code == 404
    assert len(await get_auto_flussi_corso(client)) == 0
    assert (await client.get(f"/api/v1/ricevute/{ricevuta_id}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_pagamento_not_found(client: AsyncClient):
    response = await client.delete(f"{BASE}/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_pagamento_anno_chiuso_409(client: AsyncClient):
    cfg = await setup_pagamento_env(client)
    iscrizione = await setup_iscrizione_corso(client)
    pagamento = await create_pagamento(client, iscrizione["id"])

    close_resp = await client.post(f"{CFG_BASE}/{cfg['id']}/chiudi")
    assert close_resp.status_code == 200

    response = await client.delete(f"{BASE}/{pagamento['id']}")
    assert response.status_code == 409

    # Flusso e ricevuta devono restare intatti
    assert len(await get_auto_flussi_corso(client)) == 1


# ── RBAC ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_pagamenti_forbidden_without_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user()
    response = await client.get(f"{BASE}/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_pagamenti_succeeds_with_corsi_read_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    response = await client.get(f"{BASE}/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_pagamento_forbidden_without_write_permission(client: AsyncClient):
    await setup_pagamento_env(client)
    iscrizione = await setup_iscrizione_corso(client)

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    response = await client.post(f"{BASE}/", json=pagamento_payload(iscrizione["id"]))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_pagamento_ok_con_corsi_write_permission(client: AsyncClient):
    await setup_pagamento_env(client)
    iscrizione = await setup_iscrizione_corso(client)

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:write"})
    response = await client.post(f"{BASE}/", json=pagamento_payload(iscrizione["id"]))
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_pagamenti_corso_requires_authentication(client: AsyncClient):
    app.dependency_overrides.pop(get_current_user, None)
    response = await client.get(f"{BASE}/")
    assert response.status_code == 401
