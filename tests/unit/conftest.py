"""Unit-test fixtures shared across all tests in this directory."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lookups import SezioneRendiconto, SottovoceRendiconto, VoceRendiconto
from app.models.macro_sezione import MacroSezione
from app.models.relations import voci_sottovoci_rendiconto

# Dati di riferimento del rendiconto, allineati a legacy_db/seed_pass2b_postgres.sql
# (e alla migrazione a7d2f1c93b08). Il DB di test è vuoto e non esegue le
# migrazioni/seed, quindi li ricreiamo qui.
_SEZIONI: list[tuple[int, str]] = [
    (1, "Uscite"),
    (2, "Entrate"),
    (3, "Fuori Bilancio"),
    (4, "Costi e proventi figurativi"),
]

# (codice, descrizione, sezione_codice). La voce legacy 7 (doppione della 5) è
# stata rimossa; la voce 15 raccoglie le sottovoci 48/49.
_VOCI: list[tuple[int, str, int]] = [
    (1, "A) Uscite da attività di interesse generale", 1),
    (2, "A) Entrate da attività di interesse generale", 2),
    (3, "B) Uscite da attività diverse", 1),
    (4, "B) Entrate da attività diverse", 2),
    (5, "C) Uscite da attività di raccolta fondi", 1),
    (6, "C) Entrate da attività di raccolta fondi", 2),
    (8, "D) Uscite da attività finanziarie e patrimoniali", 1),
    (9, "D) Entrate da attività finanziarie e patrimoniali", 2),
    (10, "E) Uscite di supporto generale", 1),
    (11, "E) Entrate di supporto generale", 2),
    (
        12,
        "Uscite da investimenti in immobilizzazioni o da deflussi di capitale di terzi",
        1,
    ),  # noqa: E501
    (
        13,
        "Entrate da disinvestimenti in immobilizzazioni o da flussi "
        "di capitale di terzi",
        2,
    ),
    (14, "Fuori Bilancio", 3),
    (15, "Costi e proventi figurativi", 4),
]

_SOTTOVOCI: list[tuple[int, str]] = [
    (1, "1) Materie prime, sussidiarie, di consumo e di merci"),
    (2, "2) Servizi"),
    (3, "3) Godimento beni di terzi"),
    (4, "4) Personale"),
    (5, "5) Uscite diverse di gestione"),
    (6, "1) Entrate da quote associative e apporti dei fondatori"),
    (7, "2) Entrate dagli associati per attività mutuali"),
    (8, "3) Entrate per prestazioni e cessioni ad associati e fondatori"),
    (9, "4) Erogazioni liberali"),
    (10, "5) Entrate del 5 per mille"),
    (11, "6) Contributi da soggetti privati"),
    (12, "7) Entrate per prestazioni e cessioni a terzi"),
    (13, "8) Contributi da enti pubblici"),
    (14, "9) Entrate da contratti con enti pubblici"),
    (15, "10) Altre entrate"),
    (16, "1) Entrate per prestazioni e cessioni ad associati e fondatori"),
    (17, "2) Contributi da soggetti privati"),
    (18, "3) Entrate per prestazioni e cessioni a terzi"),
    (19, "4) Contributi da enti pubblici"),
    (20, "5) Entrate da contratti con enti pubblici"),
    (21, "6) Altre entrate"),
    (22, "1) Uscite per raccolte fondi abituali"),
    (23, "2) Uscite per raccolte fondi occasionali"),
    (24, "3) Altre uscite"),
    (25, "1) Entrate da raccolte fondi abituali"),
    (26, "2) Entrate da raccolte fondi occasionali"),
    (27, "3) Altre entrate"),
    (28, "1) Su rapporti bancari"),
    (29, "2) Su investimenti finanziari"),
    (30, "3) Su patrimonio edilizio"),
    (31, "4) Su altri beni patrimoniali"),
    (32, "5) Altre uscite"),
    (33, "1) Da rapporti bancari"),
    (34, "2) Da altri investimenti finanziari"),
    (35, "3) Da patrimonio edilizio"),
    (36, "4) Da altri beni patrimoniali"),
    (37, "5) Altre entrate"),
    (38, "1) Entrate da distacco del personale"),
    (39, "2) Altre entrate di supporto generale"),
    (
        40,
        "1) Investimenti in immobilizzazioni inerenti alle attività di "
        "interesse generale",
    ),
    (41, "2) Investimenti in immobilizzazioni inerenti alle attività diverse"),
    (42, "3) Investimenti in attività finanziarie e patrimoniali"),
    (43, "4) Rimborso di finanziamenti per quota capitale e di prestiti"),
    (
        44,
        (
            "1) Disinvestimenti di immobilizzazioni inerenti alle attività di "
            "interesse generale"
        ),
    ),
    (45, "2) Disinvestimenti di immobilizzazioni inerenti alle attività diverse"),
    (46, "3) Disinvestimenti di attività finanziarie e patrimoniali"),
    (47, "4) Ricevimento di finanziamenti e di prestiti"),
    (48, "1) da attività di interesse generale"),
    (49, "2) da attività diverse"),
    (50, "Fuori Bilancio"),
]

# voce.codice → [sottovoce.codice]. Le sottovoci generiche di uscita (1-5) sono
# condivise da A/B/E Uscite (voci 1, 3, 10).
_JUNCTION: dict[int, list[int]] = {
    1: [1, 2, 3, 4, 5],
    2: [6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    3: [1, 2, 3, 4, 5],
    4: [16, 17, 18, 19, 20, 21],
    5: [22, 23, 24],
    6: [25, 26, 27],
    8: [28, 29, 30, 31, 32],
    9: [33, 34, 35, 36, 37],
    10: [1, 2, 3, 4, 5],
    11: [38, 39],
    12: [40, 41, 42, 43],
    13: [44, 45, 46, 47],
    14: [50],
    15: [48, 49],
}


@pytest.fixture
async def seeded_macro_sezioni(db_session: AsyncSession) -> None:
    """Seed the four fixed macro-sezioni used by archivio tests."""
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


@pytest.fixture(autouse=True)
async def seed_rendiconto_lookups(setup_db: None, db_session: AsyncSession) -> None:
    """Seed the rendiconto reference data (sezioni, voci, sottovoci e la tabella
    ponte voce↔sottovoce). In produzione vivono in seed_pass2b_postgres.sql; il
    DB di test parte vuoto, quindi le ricreiamo identiche."""
    db_session.add_all(
        [SezioneRendiconto(codice=c, descrizione=d) for c, d in _SEZIONI]
    )
    db_session.add_all(
        [
            VoceRendiconto(codice=c, descrizione=d, sezione_codice=sez)
            for c, d, sez in _VOCI
        ]
    )
    db_session.add_all(
        [SottovoceRendiconto(codice=c, descrizione=d) for c, d in _SOTTOVOCI]
    )
    await db_session.flush()

    await db_session.execute(
        voci_sottovoci_rendiconto.insert(),
        [
            {"voce_codice": voce, "sottovoce_codice": sv}
            for voce, sottovoci in _JUNCTION.items()
            for sv in sottovoci
        ],
    )
    await db_session.commit()
