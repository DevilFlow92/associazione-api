from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient

CFG_BASE = "/api/v1/configurazioni-banda-anno"
FLUSSO_BASE = "/api/v1/flussi-cassa"
REND_BASE = "/api/v1/contabilita/rendiconto"


async def setup_rendiconto_env(
    client: AsyncClient, banda_codice: int = 1, anno: int = 2026
) -> dict:
    """Seed NaturaFlusso lookups
    + create ConfigurazioneBandaAnno (which seeds VoceContabilita).

    Returns {"cfg": cfg_json, "voci": {name: voce_json}}.
    """
    await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Banca"}
    )
    await client.post(
        "/api/v1/nature-flusso/", json={"codice": 2, "descrizione": "Cassa"}
    )

    cfg_resp = await client.post(
        f"{CFG_BASE}/", json={"banda_codice": banda_codice, "anno": anno}
    )
    assert cfg_resp.status_code == 201, cfg_resp.text
    cfg = cfg_resp.json()

    voci_resp = await client.get(
        f"/api/v1/voci-contabilita/?banda_codice={banda_codice}&limit=100"
    )
    assert voci_resp.status_code == 200
    voci = {v["voce_contabilita"]: v for v in voci_resp.json()["items"]}
    return {"cfg": cfg, "voci": voci}


def flusso_payload(voce_id: int, natura_codice: int = 1, **overrides) -> dict:
    payload = {
        "data_registrazione": "2026-01-15T00:00:00",
        "descrizione_operazione": "Test flusso",
        "voce_contabilita_id": voce_id,
        "importo": 100.0,
        "segno": "+",
        "natura_flusso_codice": natura_codice,
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_rendiconto_empty_anno(client: AsyncClient):
    """Config exists with saldi iniziali, no flussi → all sezioni totale=0
    saldi_finali==saldi_iniziali."""
    env = await setup_rendiconto_env(client)
    cfg_id = env["cfg"]["id"]

    await client.patch(
        f"{CFG_BASE}/{cfg_id}",
        json={"saldo_iniziale_cassa": "150.00", "saldo_iniziale_banca": "300.00"},
    )

    resp = await client.get(f"{REND_BASE}/?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    data = resp.json()

    assert data["banda_codice"] == 1
    assert data["anno"] == 2026
    assert data["chiuso"] is False
    assert Decimal(data["saldo_iniziale_cassa"]) == Decimal("150")
    assert Decimal(data["saldo_iniziale_banca"]) == Decimal("300")

    # Full Modello D skeleton always returned from lookup tables (4 sezioni), all zero
    assert len(data["sezioni"]) == 4
    for sezione in data["sezioni"]:
        assert Decimal(sezione["totale"]) == Decimal(0)

    assert Decimal(data["totali"]["entrate"]) == Decimal(0)
    assert Decimal(data["totali"]["uscite"]) == Decimal(0)
    assert Decimal(data["totali"]["avanzo_disavanzo"]) == Decimal(0)
    assert Decimal(data["totali"]["saldo_finale_cassa"]) == Decimal("150")
    assert Decimal(data["totali"]["saldo_finale_banca"]) == Decimal("300")


@pytest.mark.asyncio
async def test_rendiconto_no_config(client: AsyncClient):
    """No config, no flussi → saldi iniziali=0, chiuso=False, all sezioni totale=0."""
    resp = await client.get(f"{REND_BASE}/?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    data = resp.json()

    assert data["chiuso"] is False
    assert Decimal(data["saldo_iniziale_cassa"]) == Decimal(0)
    assert Decimal(data["saldo_iniziale_banca"]) == Decimal(0)
    # Full skeleton always returned from lookup tables;
    # all totals are zero without flussi
    assert len(data["sezioni"]) == 4
    for sezione in data["sezioni"]:
        assert Decimal(sezione["totale"]) == Decimal(0)
    assert Decimal(data["totali"]["entrate"]) == Decimal(0)
    assert Decimal(data["totali"]["uscite"]) == Decimal(0)
    assert Decimal(data["totali"]["avanzo_disavanzo"]) == Decimal(0)


@pytest.mark.asyncio
async def test_rendiconto_aggregates_correctly(client: AsyncClient):
    """3 flussi
    (entrata, uscita, fuori bilancio) → correct aggregation at every level."""
    env = await setup_rendiconto_env(client)
    voci = env["voci"]

    # Entrata: 100 in Entrate sezione
    await client.post(
        f"{FLUSSO_BASE}/",
        json=flusso_payload(voci["Quote associative"]["id"], importo=100.0, segno="+"),
    )
    # Uscita: 30 in Uscite sezione
    await client.post(
        f"{FLUSSO_BASE}/",
        json=flusso_payload(voci["Spese bancarie"]["id"], importo=30.0, segno="-"),
    )
    # Fuori bilancio: 50
    await client.post(
        f"{FLUSSO_BASE}/",
        json=flusso_payload(voci["Saldo iniziale"]["id"], importo=50.0, segno="+"),
    )

    resp = await client.get(f"{REND_BASE}/?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    data = resp.json()

    by_desc = {s["descrizione"]: s for s in data["sezioni"]}

    sez_entrate = by_desc["Entrate"]
    assert Decimal(sez_entrate["totale"]) == Decimal("100")
    assert Decimal(sez_entrate["voci"][0]["totale"]) == Decimal("100")
    assert Decimal(sez_entrate["voci"][0]["sottovoci"][0]["totale"]) == Decimal("100")

    sez_uscite = by_desc["Uscite"]
    assert Decimal(sez_uscite["totale"]) == Decimal("-30")

    sez_fb = by_desc["Fuori Bilancio"]
    assert Decimal(sez_fb["totale"]) == Decimal("50")

    assert Decimal(data["totali"]["entrate"]) == Decimal("100")
    assert Decimal(data["totali"]["uscite"]) == Decimal("30")
    assert Decimal(data["totali"]["avanzo_disavanzo"]) == Decimal("70")


@pytest.mark.asyncio
async def test_rendiconto_fuori_bilancio_excluded_from_totali(client: AsyncClient):
    """Flusso in Fuori Bilancio appears in sezioni but not in totali.entrate/uscite."""
    env = await setup_rendiconto_env(client)
    voci = env["voci"]

    await client.post(
        f"{FLUSSO_BASE}/",
        json=flusso_payload(voci["Saldo iniziale"]["id"], importo=200.0, segno="+"),
    )

    resp = await client.get(f"{REND_BASE}/?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    data = resp.json()

    by_desc = {s["descrizione"]: s for s in data["sezioni"]}
    assert "Fuori Bilancio" in by_desc
    assert Decimal(by_desc["Fuori Bilancio"]["totale"]) == Decimal("200")

    assert Decimal(data["totali"]["entrate"]) == Decimal(0)
    assert Decimal(data["totali"]["uscite"]) == Decimal(0)
    assert Decimal(data["totali"]["avanzo_disavanzo"]) == Decimal(0)


@pytest.mark.asyncio
async def test_rendiconto_saldi_finali_includono_flussi_cassa_e_banca(
    client: AsyncClient,
):
    """saldo_finale = saldo_iniziale + flussi per natura (cassa/banca)."""
    env = await setup_rendiconto_env(client)
    cfg_id = env["cfg"]["id"]
    voce_id = env["voci"]["Spese bancarie"]["id"]

    await client.patch(
        f"{CFG_BASE}/{cfg_id}",
        json={"saldo_iniziale_cassa": "100.00", "saldo_iniziale_banca": "200.00"},
    )

    # Cassa +50
    await client.post(
        f"{FLUSSO_BASE}/",
        json=flusso_payload(voce_id, natura_codice=2, importo=50.0, segno="+"),
    )
    # Banca -30
    await client.post(
        f"{FLUSSO_BASE}/",
        json=flusso_payload(voce_id, natura_codice=1, importo=30.0, segno="-"),
    )

    resp = await client.get(f"{REND_BASE}/?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    data = resp.json()

    assert Decimal(data["totali"]["saldo_finale_cassa"]) == Decimal("150")
    assert Decimal(data["totali"]["saldo_finale_banca"]) == Decimal("170")


@pytest.mark.asyncio
async def test_rendiconto_signed_segni(client: AsyncClient):
    """'+' adds and '-' subtracts: totale voce/sezione reflects net signed importo."""
    env = await setup_rendiconto_env(client)
    voce_id = env["voci"]["Quote associative"]["id"]

    await client.post(
        f"{FLUSSO_BASE}/", json=flusso_payload(voce_id, importo=100.0, segno="+")
    )
    await client.post(
        f"{FLUSSO_BASE}/", json=flusso_payload(voce_id, importo=30.0, segno="-")
    )

    resp = await client.get(f"{REND_BASE}/?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    data = resp.json()

    by_desc = {s["descrizione"]: s for s in data["sezioni"]}
    sez_entrate = by_desc["Entrate"]

    assert Decimal(sez_entrate["voci"][0]["totale"]) == Decimal("70")
    assert Decimal(sez_entrate["totale"]) == Decimal("70")

    # Raw signed importi: +100 and -30 → entrate=100, uscite=30, avanzo=70
    assert Decimal(data["totali"]["entrate"]) == Decimal("100")
    assert Decimal(data["totali"]["uscite"]) == Decimal("30")
    assert Decimal(data["totali"]["avanzo_disavanzo"]) == Decimal("70")


@pytest.mark.asyncio
async def test_rendiconto_filter_per_banda_e_anno(client: AsyncClient):
    """Flussi from other banda or other anno are excluded from the rendiconto."""
    env = await setup_rendiconto_env(client, banda_codice=1, anno=2026)
    voce_1 = env["voci"]["Quote associative"]

    # Config for banda=2 (nature already created by setup_rendiconto_env)
    cfg2_resp = await client.post(
        f"{CFG_BASE}/", json={"banda_codice": 2, "anno": 2026}
    )
    assert cfg2_resp.status_code == 201
    voci2_resp = await client.get("/api/v1/voci-contabilita/?banda_codice=2&limit=100")
    voce_2 = next(
        v
        for v in voci2_resp.json()["items"]
        if v["voce_contabilita"] == "Quote associative"
    )

    # Flusso banda=1, anno=2026 → should appear
    await client.post(
        f"{FLUSSO_BASE}/", json=flusso_payload(voce_1["id"], importo=100.0)
    )
    # Flusso banda=2, anno=2026 → excluded (different banda)
    await client.post(
        f"{FLUSSO_BASE}/", json=flusso_payload(voce_2["id"], importo=999.0)
    )
    # Flusso banda=1, anno=2025 → excluded (different anno)
    await client.post(
        f"{FLUSSO_BASE}/",
        json=flusso_payload(
            voce_1["id"],
            importo=50.0,
            data_registrazione="2025-06-15T00:00:00",
        ),
    )

    resp = await client.get(f"{REND_BASE}/?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    data = resp.json()

    assert Decimal(data["totali"]["entrate"]) == Decimal("100")


@pytest.mark.asyncio
async def test_rendiconto_mensile(client: AsyncClient):
    """Monthly breakdown: correct per-month buckets, fuori-bilancio excluded,
    reconciliation sum(entrate) == totali.entrate and sum(uscite) == totali.uscite."""
    env = await setup_rendiconto_env(client)
    voci = env["voci"]

    voce_entrate_id = voci["Quote associative"]["id"]
    voce_uscite_id = voci["Spese bancarie"]["id"]
    voce_fb_id = voci["Saldo iniziale"]["id"]

    # Gennaio: entrata 100, uscita 40
    await client.post(
        f"{FLUSSO_BASE}/",
        json=flusso_payload(
            voce_entrate_id,
            importo=100.0,
            segno="+",
            data_registrazione="2026-01-10T00:00:00",
        ),
    )
    await client.post(
        f"{FLUSSO_BASE}/",
        json=flusso_payload(
            voce_uscite_id,
            importo=40.0,
            segno="-",
            data_registrazione="2026-01-20T00:00:00",
        ),
    )
    # Marzo: entrata 200
    await client.post(
        f"{FLUSSO_BASE}/",
        json=flusso_payload(
            voce_entrate_id,
            importo=200.0,
            segno="+",
            data_registrazione="2026-03-05T00:00:00",
        ),
    )
    # Fuori bilancio in gennaio: should NOT count
    await client.post(
        f"{FLUSSO_BASE}/",
        json=flusso_payload(
            voce_fb_id,
            importo=50.0,
            segno="+",
            data_registrazione="2026-01-15T00:00:00",
        ),
    )

    resp = await client.get(f"{REND_BASE}/mensile?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    data = resp.json()

    assert data["banda_codice"] == 1
    assert data["anno"] == 2026

    mensile = data["mensile"]
    assert len(mensile) == 12

    by_mese = {item["mese"]: item for item in mensile}

    jan = by_mese[1]
    assert Decimal(jan["entrate"]) == Decimal("100")
    assert Decimal(jan["uscite"]) == Decimal("40")

    mar = by_mese[3]
    assert Decimal(mar["entrate"]) == Decimal("200")
    assert Decimal(mar["uscite"]) == Decimal("0")

    for m in range(1, 13):
        if m not in (1, 3):
            assert Decimal(by_mese[m]["entrate"]) == Decimal("0")
            assert Decimal(by_mese[m]["uscite"]) == Decimal("0")

    # Reconciliation: sums must match the full rendiconto totali
    full_resp = await client.get(f"{REND_BASE}/?banda_codice=1&anno=2026")
    assert full_resp.status_code == 200
    totali = full_resp.json()["totali"]

    assert sum(Decimal(item["entrate"]) for item in mensile) == Decimal(
        totali["entrate"]
    )
    assert sum(Decimal(item["uscite"]) for item in mensile) == Decimal(totali["uscite"])


@pytest.mark.asyncio
async def test_rendiconto_chiuso_flag(client: AsyncClient):
    """ConfigurazioneBandaAnno.chiuso=True is reflected in response.chiuso."""
    env = await setup_rendiconto_env(client)
    cfg_id = env["cfg"]["id"]

    close_resp = await client.post(f"{CFG_BASE}/{cfg_id}/chiudi")
    assert close_resp.status_code == 200

    resp = await client.get(f"{REND_BASE}/?banda_codice=1&anno=2026")
    assert resp.status_code == 200
    assert resp.json()["chiuso"] is True
