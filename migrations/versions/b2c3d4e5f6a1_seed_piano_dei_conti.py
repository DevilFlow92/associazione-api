"""Seed piano dei conti — sezioni, voci, sottovoci rendiconto e voci contabilità

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-06-28 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a1"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEZIONI = [
    (1, "Uscite"),
    (2, "Entrate"),
    (3, "Fuori Bilancio"),
    (4, "Costi e proventi figurativi"),
]

VOCI = [
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
    ),
    (
        13,
        "Entrate da disinvestimenti in immobilizzazioni o da flussi di "
        "capitale di terzi",
        2,
    ),
    (14, "Fuori Bilancio", 3),
    (15, "Costi e proventi figurativi", 4),
]

SOTTOVOCI = [
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
        "1) Disinvestimenti di immobilizzazioni inerenti alle attività di "
        "interesse generale",
    ),
    (45, "2) Disinvestimenti di immobilizzazioni inerenti alle attività diverse"),
    (46, "3) Disinvestimenti di attività finanziarie e patrimoniali"),
    (47, "4) Ricevimento di finanziamenti e di prestiti"),
    (48, "1) da attività di interesse generale"),
    (49, "2) da attività diverse"),
    (50, "Fuori Bilancio"),
]

VOCI_SOTTOVOCI = [
    (1, 1),
    (1, 2),
    (1, 3),
    (1, 4),
    (1, 5),
    (2, 6),
    (2, 7),
    (2, 8),
    (2, 9),
    (2, 10),
    (2, 11),
    (2, 12),
    (2, 13),
    (2, 14),
    (2, 15),
    (3, 1),
    (3, 2),
    (3, 3),
    (3, 4),
    (3, 5),
    (4, 16),
    (4, 17),
    (4, 18),
    (4, 19),
    (4, 20),
    (4, 21),
    (5, 22),
    (5, 23),
    (5, 24),
    (6, 25),
    (6, 26),
    (6, 27),
    (8, 28),
    (8, 29),
    (8, 30),
    (8, 31),
    (8, 32),
    (9, 33),
    (9, 34),
    (9, 35),
    (9, 36),
    (9, 37),
    (10, 1),
    (10, 2),
    (10, 3),
    (10, 4),
    (10, 5),
    (11, 38),
    (11, 39),
    (12, 40),
    (12, 41),
    (12, 42),
    (12, 43),
    (13, 44),
    (13, 45),
    (13, 46),
    (13, 47),
    (14, 50),
    (15, 48),
    (15, 49),
]

VOCI_CONTABILITA = [
    (1, "Assicurazione", 1, 1, 2),
    (2, "Collaboratori artistici art.67", 1, 1, 2),
    (3, "Contributo da Comune di Quartu Sant'Elena", 2, 2, 13),
    (4, "Corsi vs. Associati", 2, 2, 7),
    (5, "Erogazioni liberali ricevute", 2, 2, 9),
    (6, "Incassi da servizi", 2, 2, 12),
    (7, "Prelievo dal c/c bancario", 3, 14, 50),
    (8, "Quote associative", 2, 2, 6),
    (9, "Spese Bancarie", 1, 8, 28),
    (
        10,
        "Servizi Diversi (neloggio mezzi, stampa locandine, pulizia divise, "
        "altri oneri)",
        1,
        1,
        2,
    ),
    (11, "SIAE", 1, 1, 2),
    (12, "Spese di rappresentanza", 1, 3, 2),
    (13, "Versamento in banca", 3, 14, 50),
]


def upgrade() -> None:
    bind = op.get_bind()

    # sezioni_rendiconto
    for codice, descrizione in SEZIONI:
        bind.execute(
            sa.text(
                "INSERT INTO sezioni_rendiconto (codice, descrizione) "
                "VALUES (:c, :d) ON CONFLICT DO NOTHING"
            ),
            {"c": codice, "d": descrizione},
        )

    # voci_rendiconto
    for codice, descrizione, sezione_codice in VOCI:
        bind.execute(
            sa.text(
                "INSERT INTO voci_rendiconto "
                "(codice, descrizione, sezione_codice) "
                "VALUES (:c, :d, :s) ON CONFLICT DO NOTHING"
            ),
            {"c": codice, "d": descrizione, "s": sezione_codice},
        )

    # sottovoci_rendiconto
    for codice, descrizione in SOTTOVOCI:
        bind.execute(
            sa.text(
                "INSERT INTO sottovoci_rendiconto (codice, descrizione) "
                "VALUES (:c, :d) ON CONFLICT DO NOTHING"
            ),
            {"c": codice, "d": descrizione},
        )

    # voci_sottovoci_rendiconto
    for voce_codice, sottovoce_codice in VOCI_SOTTOVOCI:
        bind.execute(
            sa.text(
                "INSERT INTO voci_sottovoci_rendiconto "
                "(voce_codice, sottovoce_codice) "
                "VALUES (:v, :s) ON CONFLICT DO NOTHING"
            ),
            {"v": voce_codice, "s": sottovoce_codice},
        )

    # voci_contabilita — banda_codice=1 (unica banda in produzione)
    for id_, voce, sezione, voce_r, sottovoce_r in VOCI_CONTABILITA:
        bind.execute(
            sa.text(
                "INSERT INTO voci_contabilita ("
                "id, banda_codice, voce_contabilita, sezione_rendiconto_codice, "
                "voce_rendiconto_codice, sottovoce_rendiconto_codice) "
                "VALUES (:id, 1, :v, :s, :vr, :sr) ON CONFLICT DO NOTHING"
            ),
            {"id": id_, "v": voce, "s": sezione, "vr": voce_r, "sr": sottovoce_r},
        )

    # Reset sequence per voci_contabilita per evitare conflitti su insert futuri
    bind.execute(
        sa.text(
            "SELECT setval('voci_contabilita_id_seq', "
            "(SELECT MAX(id) FROM voci_contabilita))"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM voci_contabilita WHERE banda_codice = 1 AND id <= 13")
    )
    bind.execute(sa.text("DELETE FROM voci_sottovoci_rendiconto"))
    bind.execute(sa.text("DELETE FROM sottovoci_rendiconto"))
    bind.execute(sa.text("DELETE FROM voci_rendiconto"))
    bind.execute(sa.text("DELETE FROM sezioni_rendiconto"))
