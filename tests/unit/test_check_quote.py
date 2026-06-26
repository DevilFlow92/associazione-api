from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient

CFG_BASE = "/api/v1/configurazioni-banda-anno"
CHECK_BASE = "/api/v1/contabilita/check-quote"

CODICE_DA_PAGARE = 1
CODICE_PAGATA = 2


async def seed_stati(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/stati-iscrizione/",
        json={"codice": CODICE_DA_PAGARE, "descrizione": "Da pagare"},
    )
    await client.post(
        "/api/v1/stati-iscrizione/",
        json={"codice": CODICE_PAGATA, "descrizione": "Pagata"},
    )


async def setup_config(
    client: AsyncClient,
    quota: str = "80.00",
    banda_codice: int = 1,
    anno: int = 2026,
) -> dict:
    """Create a ConfigurazioneBandaAnno with quota_annuale_attesa set, a 'Banca'
    natura, and voce_contabilita_quote_id linked (so paid iscrizioni can be
    created via the API). Returns the patched config json."""
    await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Banca"}
    )
    cfg_resp = await client.post(
        f"{CFG_BASE}/",
        json={
            "banda_codice": banda_codice,
            "anno": anno,
            "quota_annuale_attesa": quota,
        },
    )
    assert cfg_resp.status_code == 201, cfg_resp.text
    cfg = cfg_resp.json()

    voci_resp = await client.get(
        f"/api/v1/voci-contabilita/?banda_codice={banda_codice}&limit=100"
    )
    voce_quote = next(
        v
        for v in voci_resp.json()["items"]
        if v["voce_contabilita"] == "Quote associative"
    )
    patch_resp = await client.patch(
        f"{CFG_BASE}/{cfg['id']}",
        json={"voce_contabilita_quote_id": voce_quote["id"]},
    )
    assert patch_resp.status_code == 200, patch_resp.text
    return patch_resp.json()


async def create_socio(
    client: AsyncClient,
    codice_socio: str,
    nome: str,
    cognome: str,
    banda_codice: int = 1,
) -> dict:
    persona = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": banda_codice, "nome": nome, "cognome": cognome},
    )
    resp = await client.post(
        "/api/v1/soci/",
        json={
            "persona_id": persona.json()["id"],
            "codice_socio": codice_socio,
            "ruolo_banda_codice": 10,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_iscrizione(
    client: AsyncClient,
    socio_id: int,
    quota: float,
    stato_codice: int = CODICE_PAGATA,
    anno: int = 2026,
    data: str = "2026-01-10",
) -> None:
    resp = await client.post(
        "/api/v1/iscrizioni/",
        json={
            "socio_id": socio_id,
            "anno": anno,
            "quota_partecipazione": quota,
            "stato_iscrizione_codice": stato_codice,
            "data_iscrizione": data,
        },
    )
    assert resp.status_code == 201, resp.text


@pytest.mark.asyncio
async def test_check_quote_no_config(client: AsyncClient):
    """No config → quota_annuale_attesa=0 and every socio is NON_DOVUTA."""
    await create_socio(client, "S001", "Mario", "Rossi")

    resp = await client.get(f"{CHECK_BASE}/?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    data = resp.json()

    assert data["banda_codice"] == 1
    assert data["anno"] == 2026
    assert Decimal(data["quota_annuale_attesa"]) == Decimal(0)
    assert len(data["soci"]) == 1
    assert data["soci"][0]["stato"] == "NON_DOVUTA"
    assert Decimal(data["soci"][0]["differenza"]) == Decimal(0)
    assert data["totali"]["soci_non_dovuta"] == 1


@pytest.mark.asyncio
async def test_check_quote_no_soci(client: AsyncClient):
    """Config exists but no soci → empty list, zeroed totali."""
    await setup_config(client, quota="80.00")

    resp = await client.get(f"{CHECK_BASE}/?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    data = resp.json()

    assert Decimal(data["quota_annuale_attesa"]) == Decimal("80")
    assert data["soci"] == []
    assert Decimal(data["totali"]["totale_atteso"]) == Decimal(0)
    assert Decimal(data["totali"]["totale_versato"]) == Decimal(0)
    assert Decimal(data["totali"]["totale_mancante"]) == Decimal(0)
    assert data["totali"]["soci_ok"] == 0


@pytest.mark.asyncio
async def test_check_quote_socio_ok(client: AsyncClient):
    """Versato == atteso → OK, differenza 0."""
    await seed_stati(client)
    await setup_config(client, quota="80.00")
    socio = await create_socio(client, "S001", "Mario", "Rossi")
    await create_iscrizione(client, socio["id"], quota=80.0)

    resp = await client.get(f"{CHECK_BASE}/?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    riga = resp.json()["soci"][0]
    assert riga["stato"] == "OK"
    assert Decimal(riga["quota_versata"]) == Decimal("80")
    assert Decimal(riga["differenza"]) == Decimal(0)


@pytest.mark.asyncio
async def test_check_quote_socio_parziale(client: AsyncClient):
    """0 < versato < atteso → PARZIALE."""
    await seed_stati(client)
    await setup_config(client, quota="80.00")
    socio = await create_socio(client, "S001", "Mario", "Rossi")
    await create_iscrizione(client, socio["id"], quota=50.0)

    resp = await client.get(f"{CHECK_BASE}/?banda_codice=1&anno=2026")
    riga = resp.json()["soci"][0]
    assert riga["stato"] == "PARZIALE"
    assert Decimal(riga["quota_versata"]) == Decimal("50")
    assert Decimal(riga["differenza"]) == Decimal("30")


@pytest.mark.asyncio
async def test_check_quote_socio_mancante(client: AsyncClient):
    """No paid iscrizione → MANCANTE, differenza == quota_attesa."""
    await seed_stati(client)
    await setup_config(client, quota="80.00")
    await create_socio(client, "S001", "Mario", "Rossi")

    resp = await client.get(f"{CHECK_BASE}/?banda_codice=1&anno=2026")
    riga = resp.json()["soci"][0]
    assert riga["stato"] == "MANCANTE"
    assert Decimal(riga["quota_versata"]) == Decimal(0)
    assert Decimal(riga["differenza"]) == Decimal("80")


@pytest.mark.asyncio
async def test_check_quote_socio_sovrappiu(client: AsyncClient):
    """Versato > atteso → SOVRAPPIU, differenza negativa."""
    await seed_stati(client)
    await setup_config(client, quota="80.00")
    socio = await create_socio(client, "S001", "Mario", "Rossi")
    await create_iscrizione(client, socio["id"], quota=100.0)

    resp = await client.get(f"{CHECK_BASE}/?banda_codice=1&anno=2026")
    riga = resp.json()["soci"][0]
    assert riga["stato"] == "SOVRAPPIU"
    assert Decimal(riga["quota_versata"]) == Decimal("100")
    assert Decimal(riga["differenza"]) == Decimal("-20")


@pytest.mark.asyncio
async def test_check_quote_iscrizione_non_pagata_non_conta(client: AsyncClient):
    """Iscrizione 'Da pagare' is not counted in quota_versata."""
    await seed_stati(client)
    await setup_config(client, quota="80.00")
    socio = await create_socio(client, "S001", "Mario", "Rossi")
    await create_iscrizione(
        client, socio["id"], quota=80.0, stato_codice=CODICE_DA_PAGARE
    )

    resp = await client.get(f"{CHECK_BASE}/?banda_codice=1&anno=2026")
    riga = resp.json()["soci"][0]
    assert riga["stato"] == "MANCANTE"
    assert Decimal(riga["quota_versata"]) == Decimal(0)


@pytest.mark.asyncio
async def test_check_quote_filtra_per_anno(client: AsyncClient):
    """A paid iscrizione of another year is not summed for the queried year."""
    await seed_stati(client)
    await setup_config(client, quota="80.00", anno=2026)
    await setup_config(client, quota="80.00", anno=2025)
    socio = await create_socio(client, "S001", "Mario", "Rossi")
    # Paid iscrizione for 2025 only
    await create_iscrizione(
        client, socio["id"], quota=80.0, anno=2025, data="2025-01-10"
    )

    resp = await client.get(f"{CHECK_BASE}/?banda_codice=1&anno=2026")
    riga = resp.json()["soci"][0]
    assert riga["stato"] == "MANCANTE"
    assert Decimal(riga["quota_versata"]) == Decimal(0)


@pytest.mark.asyncio
async def test_check_quote_filtra_per_banda(client: AsyncClient):
    """A socio of another banda does not appear in the response."""
    await seed_stati(client)
    await setup_config(client, quota="80.00", banda_codice=1)
    await create_socio(client, "S001", "Mario", "Rossi", banda_codice=1)
    await create_socio(client, "S002", "Luigi", "Verdi", banda_codice=2)

    resp = await client.get(f"{CHECK_BASE}/?banda_codice=1&anno=2026")
    soci = resp.json()["soci"]
    assert len(soci) == 1
    assert soci[0]["codice_socio"] == "S001"


@pytest.mark.asyncio
async def test_check_quote_ordering(client: AsyncClient):
    """Soci are ordered by cognome, then nome."""
    await setup_config(client, quota="80.00")
    await create_socio(client, "S001", "Mario", "Rossi")
    await create_socio(client, "S002", "Anna", "Bianchi")
    await create_socio(client, "S003", "Carlo", "Bianchi")

    resp = await client.get(f"{CHECK_BASE}/?banda_codice=1&anno=2026")
    soci = resp.json()["soci"]
    cognomi_nomi = [(s["cognome"], s["nome"]) for s in soci]
    assert cognomi_nomi == [
        ("Bianchi", "Anna"),
        ("Bianchi", "Carlo"),
        ("Rossi", "Mario"),
    ]


@pytest.mark.asyncio
async def test_check_quote_totali_aggregati(client: AsyncClient):
    """Totals and per-stato counts aggregate correctly across soci."""
    await seed_stati(client)
    await setup_config(client, quota="80.00")

    socio_ok = await create_socio(client, "S001", "Mario", "Rossi")
    socio_parz = await create_socio(client, "S002", "Anna", "Bianchi")
    socio_sovr = await create_socio(client, "S003", "Carlo", "Verdi")
    # socio_manc has no paid iscrizione
    await create_socio(client, "S004", "Dario", "Neri")

    await create_iscrizione(client, socio_ok["id"], quota=80.0)
    await create_iscrizione(client, socio_parz["id"], quota=30.0)
    await create_iscrizione(client, socio_sovr["id"], quota=100.0)

    resp = await client.get(f"{CHECK_BASE}/?banda_codice=1&anno=2026")
    data = resp.json()
    totali = data["totali"]

    # 4 soci, each expects 80
    assert Decimal(totali["totale_atteso"]) == Decimal("320")
    # 80 + 30 + 100 + 0
    assert Decimal(totali["totale_versato"]) == Decimal("210")
    # max(diff,0): OK=0, parziale=50, sovrappiu=0, mancante=80 → 130
    assert Decimal(totali["totale_mancante"]) == Decimal("130")

    assert totali["soci_ok"] == 1
    assert totali["soci_parziale"] == 1
    assert totali["soci_sovrappiu"] == 1
    assert totali["soci_mancante"] == 1
    assert totali["soci_non_dovuta"] == 0
