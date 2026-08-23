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


async def create_tipo_corso(
    client: AsyncClient, codice: int = 1, descrizione: str = "Ottoni"
) -> dict:
    response = await client.post(
        "/api/v1/tipi-corso/", json={"codice": codice, "descrizione": descrizione}
    )
    assert response.status_code == 201
    return response.json()


async def create_categoria(
    client: AsyncClient, codice: int = 1, descrizione: str = "Scale"
) -> dict:
    response = await client.post(
        "/api/v1/categorie-voce-programma/",
        json={"codice": codice, "descrizione": descrizione},
    )
    assert response.status_code == 201
    return response.json()


def voce_payload(
    tipo_corso_codice: int, categoria_codice: int = 1, **overrides
) -> dict:
    payload = {
        "tipo_corso_codice": tipo_corso_codice,
        "categoria_codice": categoria_codice,
        "testo": "Scala di Do maggiore",
    }
    payload.update(overrides)
    return payload


async def create_voce(
    client: AsyncClient,
    tipo_corso_codice: int,
    categoria_codice: int = 1,
    **overrides,
) -> dict:
    response = await client.post(
        "/api/v1/catalogo-programmi/",
        json=voce_payload(tipo_corso_codice, categoria_codice, **overrides),
    )
    assert response.status_code == 201
    return response.json()


# ── CRUD happy path ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_voce_programma_catalogo(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)
    voce = await create_voce(client, tipo["codice"], categoria["codice"])

    assert voce["categoria_codice"] == categoria["codice"]
    assert voce["categoria"]["codice"] == categoria["codice"]
    assert voce["categoria"]["descrizione"] == categoria["descrizione"]
    assert voce["testo"] == "Scala di Do maggiore"
    assert voce["livello"] == 1
    assert voce["attiva"] is True
    assert voce["tipo_corso"]["codice"] == tipo["codice"]


@pytest.mark.asyncio
async def test_create_voce_programma_catalogo_livello_esplicito(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)
    voce = await create_voce(client, tipo["codice"], categoria["codice"], livello=3)

    assert voce["livello"] == 3


@pytest.mark.asyncio
async def test_get_voce_programma_catalogo(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)
    voce = await create_voce(client, tipo["codice"], categoria["codice"])

    response = await client.get(f"/api/v1/catalogo-programmi/{voce['id']}")
    assert response.status_code == 200
    assert response.json()["testo"] == "Scala di Do maggiore"


@pytest.mark.asyncio
async def test_get_voce_programma_catalogo_not_found(client: AsyncClient):
    response = await client.get("/api/v1/catalogo-programmi/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_voci_programma_catalogo_filtro_tipo_corso_e_attiva(
    client: AsyncClient,
):
    tipo_ottoni = await create_tipo_corso(client, codice=1, descrizione="Ottoni")
    tipo_ance = await create_tipo_corso(client, codice=2, descrizione="Ance")
    categoria = await create_categoria(client)
    await create_voce(
        client, tipo_ottoni["codice"], categoria["codice"], testo="Scala di Do"
    )
    voce_disattivata = await create_voce(
        client, tipo_ottoni["codice"], categoria["codice"], testo="Scala di Re"
    )
    await create_voce(
        client, tipo_ance["codice"], categoria["codice"], testo="Scala di Do"
    )

    response = await client.patch(
        f"/api/v1/catalogo-programmi/{voce_disattivata['id']}",
        json={"attiva": False},
    )
    assert response.status_code == 200

    response = await client.get(
        "/api/v1/catalogo-programmi/",
        params={"tipo_corso_codice": tipo_ottoni["codice"], "attiva": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["testo"] == "Scala di Do"


@pytest.mark.asyncio
async def test_list_voci_programma_catalogo_filtro_categoria_codice(
    client: AsyncClient,
):
    tipo = await create_tipo_corso(client)
    categoria_scale = await create_categoria(client, codice=1, descrizione="Scale")
    categoria_tecnica = await create_categoria(client, codice=2, descrizione="Tecnica")
    await create_voce(
        client, tipo["codice"], categoria_scale["codice"], testo="Scala di Do"
    )
    await create_voce(
        client, tipo["codice"], categoria_tecnica["codice"], testo="Note lunghe"
    )

    response = await client.get(
        "/api/v1/catalogo-programmi/",
        params={"categoria_codice": categoria_scale["codice"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["testo"] == "Scala di Do"


@pytest.mark.asyncio
async def test_list_voci_programma_catalogo_filtro_livello(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)
    await create_voce(
        client, tipo["codice"], categoria["codice"], testo="Scala di Do", livello=1
    )
    await create_voce(
        client, tipo["codice"], categoria["codice"], testo="Scala cromatica", livello=2
    )

    response = await client.get("/api/v1/catalogo-programmi/", params={"livello": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["testo"] == "Scala cromatica"


@pytest.mark.asyncio
async def test_update_voce_programma_catalogo(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client, codice=1, descrizione="Scale")
    categoria_tecnica = await create_categoria(client, codice=2, descrizione="Tecnica")
    voce = await create_voce(client, tipo["codice"], categoria["codice"])

    response = await client.patch(
        f"/api/v1/catalogo-programmi/{voce['id']}",
        json={"categoria_codice": categoria_tecnica["codice"], "testo": "Studio n.1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["categoria_codice"] == categoria_tecnica["codice"]
    assert data["testo"] == "Studio n.1"


@pytest.mark.asyncio
async def test_update_voce_programma_catalogo_not_found(client: AsyncClient):
    response = await client.patch(
        "/api/v1/catalogo-programmi/999", json={"testo": "tecnica"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_disattiva_voce_programma_catalogo_no_delete_fisico(
    client: AsyncClient,
):
    """Il "delete" della card è un soft-delete: PATCH attiva=False, la voce
    resta leggibile via GET (nessuna DELETE fisica esposta)."""
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)
    voce = await create_voce(client, tipo["codice"], categoria["codice"])

    response = await client.patch(
        f"/api/v1/catalogo-programmi/{voce['id']}", json={"attiva": False}
    )
    assert response.status_code == 200
    assert response.json()["attiva"] is False

    riletta = await client.get(f"/api/v1/catalogo-programmi/{voce['id']}")
    assert riletta.status_code == 200
    assert riletta.json()["attiva"] is False


@pytest.mark.asyncio
async def test_nessun_endpoint_delete_esposto(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)
    voce = await create_voce(client, tipo["codice"], categoria["codice"])

    response = await client.delete(f"/api/v1/catalogo-programmi/{voce['id']}")
    assert response.status_code == 405


# ── Violazioni ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_voce_programma_catalogo_tipo_corso_not_found(
    client: AsyncClient,
):
    categoria = await create_categoria(client)
    response = await client.post(
        "/api/v1/catalogo-programmi/", json=voce_payload(999, categoria["codice"])
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_voce_programma_catalogo_categoria_not_found(
    client: AsyncClient,
):
    tipo = await create_tipo_corso(client)
    response = await client.post(
        "/api/v1/catalogo-programmi/", json=voce_payload(tipo["codice"], 999)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_voce_programma_catalogo_duplicata(client: AsyncClient):
    """Vincolo UNIQUE (tipo_corso_codice, testo): stesso testo letterale nello
    stesso tipo corso non è ammesso."""
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)
    await create_voce(
        client, tipo["codice"], categoria["codice"], testo="Scala di Do maggiore"
    )

    response = await client.post(
        "/api/v1/catalogo-programmi/",
        json=voce_payload(
            tipo["codice"], categoria["codice"], testo="Scala di Do maggiore"
        ),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_voce_programma_catalogo_stesso_testo_tipo_corso_diverso_ok(
    client: AsyncClient,
):
    """Il vincolo UNIQUE è per tipo corso: lo stesso testo su un tipo corso
    diverso è ammesso."""
    tipo_ottoni = await create_tipo_corso(client, codice=1, descrizione="Ottoni")
    tipo_ance = await create_tipo_corso(client, codice=2, descrizione="Ance")
    categoria = await create_categoria(client)
    await create_voce(
        client, tipo_ottoni["codice"], categoria["codice"], testo="Scala di Do maggiore"
    )

    response = await client.post(
        "/api/v1/catalogo-programmi/",
        json=voce_payload(
            tipo_ance["codice"], categoria["codice"], testo="Scala di Do maggiore"
        ),
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_update_voce_programma_catalogo_duplicata(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)
    await create_voce(
        client, tipo["codice"], categoria["codice"], testo="Scala di Do maggiore"
    )
    altra = await create_voce(
        client, tipo["codice"], categoria["codice"], testo="Scala di Re maggiore"
    )

    response = await client.patch(
        f"/api/v1/catalogo-programmi/{altra['id']}",
        json={"testo": "Scala di Do maggiore"},
    )
    assert response.status_code == 409


# ── Permessi (RBAC puro, nessuna row-level) ─────────────────────────────────


@pytest.mark.asyncio
async def test_list_forbidden_senza_corsi_read(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user()
    response = await client.get("/api/v1/catalogo-programmi/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_ok_con_solo_corsi_read(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(superuser=True)
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)
    voce = await create_voce(client, tipo["codice"], categoria["codice"])

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    response = await client.get(f"/api/v1/catalogo-programmi/{voce['id']}")
    assert response.status_code == 200

    response = await client.get("/api/v1/catalogo-programmi/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_forbidden_senza_corsi_write(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(superuser=True)
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    response = await client.post(
        "/api/v1/catalogo-programmi/",
        json=voce_payload(tipo["codice"], categoria["codice"]),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_forbidden_senza_corsi_write(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(superuser=True)
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)
    voce = await create_voce(client, tipo["codice"], categoria["codice"])

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    response = await client.patch(
        f"/api/v1/catalogo-programmi/{voce['id']}", json={"testo": "tecnica"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_ok_con_corsi_write(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(superuser=True)
    tipo = await create_tipo_corso(client)
    categoria = await create_categoria(client)

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:write"})
    response = await client.post(
        "/api/v1/catalogo-programmi/",
        json=voce_payload(tipo["codice"], categoria["codice"]),
    )
    assert response.status_code == 201


# ── CategoriaVoceProgramma (lookup) ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_categoria_voce_programma(client: AsyncClient):
    response = await client.post(
        "/api/v1/categorie-voce-programma/",
        json={"codice": 1, "descrizione": "Scale"},
    )
    assert response.status_code == 201
    assert response.json() == {"codice": 1, "descrizione": "Scale"}

    response = await client.get("/api/v1/categorie-voce-programma/1")
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Scale"


@pytest.mark.asyncio
async def test_categoria_voce_programma_duplicate_codice(client: AsyncClient):
    await client.post(
        "/api/v1/categorie-voce-programma/",
        json={"codice": 1, "descrizione": "Scale"},
    )
    response = await client.post(
        "/api/v1/categorie-voce-programma/",
        json={"codice": 1, "descrizione": "Tecnica"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_categoria_voce_programma_not_found(client: AsyncClient):
    response = await client.get("/api/v1/categorie-voce-programma/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_categoria_voce_programma(client: AsyncClient):
    await client.post(
        "/api/v1/categorie-voce-programma/",
        json={"codice": 3, "descrizione": "Repertorio"},
    )
    response = await client.patch(
        "/api/v1/categorie-voce-programma/3", json={"descrizione": "Repertorio banda"}
    )
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Repertorio banda"


@pytest.mark.asyncio
async def test_delete_categoria_voce_programma(client: AsyncClient):
    await client.post(
        "/api/v1/categorie-voce-programma/",
        json={"codice": 4, "descrizione": "Teoria"},
    )
    response = await client.delete("/api/v1/categorie-voce-programma/4")
    assert response.status_code == 204
    assert (await client.get("/api/v1/categorie-voce-programma/4")).status_code == 404
