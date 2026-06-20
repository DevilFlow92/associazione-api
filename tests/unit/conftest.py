"""Unit-test fixtures shared across all tests in this directory."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lookups import SezioneRendiconto, SottovoceRendiconto, VoceRendiconto


@pytest.fixture(autouse=True)
async def seed_rendiconto_lookups(setup_db: None, db_session: AsyncSession) -> None:
    """Seed the minimum rendiconto lookup rows required by the seeding logic in
    ConfigurazioneBandaAnnoService.  These rows are present in production
    (seed_pass2b_postgres.sql) but not in the blank test database."""
    db_session.add_all(
        [
            SezioneRendiconto(codice=1, descrizione="Uscite"),
            SezioneRendiconto(codice=2, descrizione="Entrate"),
            SezioneRendiconto(codice=3, descrizione="Fuori Bilancio"),
            VoceRendiconto(
                codice=2, descrizione="A) Entrate da attività di interesse generale"
            ),
            VoceRendiconto(
                codice=8,
                descrizione="D) Uscite da attività finanziarie e patrimoniali",
            ),
            VoceRendiconto(codice=14, descrizione="Fuori Bilancio"),
            SottovoceRendiconto(
                codice=6,
                descrizione="1) Entrate da quote associative e apporti dei fondatori",
            ),
            SottovoceRendiconto(codice=28, descrizione="1) Su rapporti bancari"),
            SottovoceRendiconto(codice=50, descrizione="Fuori Bilancio"),
        ]
    )
    await db_session.commit()
