from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.macro_sezione import MacroSezione


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


async def test_list_macro_sezioni_returns_four_seeded_rows(
    client: AsyncClient, seeded_macro_sezioni: None
) -> None:
    r = await client.get("/api/v1/macro-sezioni/")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 4
    nomi = {row["nome"] for row in data}
    assert nomi == {
        "Certificazioni Uniche",
        "Verbali e Libro Soci",
        "Concorsi e Bandi",
        "Documenti Amministrativi",
    }


async def test_list_macro_sezioni_ordered_by_ordine(
    client: AsyncClient, seeded_macro_sezioni: None
) -> None:
    r = await client.get("/api/v1/macro-sezioni/")
    assert r.status_code == 200
    ordini = [row["ordine"] for row in r.json()]
    assert ordini == sorted(ordini)
