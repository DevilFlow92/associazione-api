"""rendiconto: voce→sezione (1:N) e voce↔sottovoce (N:M)

Aggiunge ``voci_rendiconto.sezione_codice`` (1:N voce→sezione), deduplica la
voce 7 (doppione verbatim della 5), introduce la sezione/voce "Costi e proventi
figurativi" per le sottovoci orfane 48/49 e crea la tabella ponte
``voci_sottovoci_rendiconto`` (N:M voce↔sottovoce) popolandola con la mappatura
del Modello D. Le sottovoci generiche di uscita (1-5) sono condivise da A/B/E
Uscite (voci 1, 3, 10).

Le operazioni dati sono guidate da JOIN/ON CONFLICT così da restare valide sia
su un DB con i lookup di produzione, sia su un DB appena migrato e vuoto.

Revision ID: a7d2f1c93b08
Revises: 5b0fd2895d05
Create Date: 2026-06-22

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7d2f1c93b08"
down_revision: str | Sequence[str] | None = "5b0fd2895d05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# voce.codice → sezione.codice (Tabella 1). Tutte alta confidenza: il prefisso
# "Uscite"/"Entrate"/"Fuori Bilancio" della descrizione determina la sezione.
_SEZIONE_BY_VOCE: dict[int, list[int]] = {
    1: [1, 3, 5, 7, 8, 10, 12],  # Uscite
    2: [2, 4, 6, 9, 11, 13],  # Entrate
    3: [14],  # Fuori Bilancio
}

# voce.codice → [sottovoce.codice] (Tabella 2 + decisioni architetturali).
# Le sottovoci 1-5 (uscite generiche) sono linkate a voci 1, 3 e 10.
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

_VOCE_7_DESCRIZIONE = "C) Uscite da attività di raccolta fondi"
_COSTI_FIGURATIVI = "Costi e proventi figurativi"


def upgrade() -> None:
    # 1. Colonna sezione_codice (nullable per consentire il backfill).
    op.add_column(
        "voci_rendiconto",
        sa.Column("sezione_codice", sa.SmallInteger(), nullable=True),
    )

    # 2. Backfill sezione_codice per le voci esistenti (no-op su DB vuoto).
    for sezione_codice, voci in _SEZIONE_BY_VOCE.items():
        codici = ", ".join(str(c) for c in voci)
        op.execute(
            f"UPDATE voci_rendiconto SET sezione_codice = {sezione_codice} "
            f"WHERE codice IN ({codici})"
        )

    # 3. Dedup voce 7 → 5: riassegna eventuali voci di contabilità, poi elimina.
    op.execute(
        "UPDATE voci_contabilita SET voce_rendiconto_codice = 5 "
        "WHERE voce_rendiconto_codice = 7"
    )
    op.execute("DELETE FROM voci_rendiconto WHERE codice = 7")

    # 4. Nuova sezione + voce "Costi e proventi figurativi" per le sottovoci 48/49.
    op.execute(
        "INSERT INTO sezioni_rendiconto (codice, descrizione) "
        f"VALUES (4, '{_COSTI_FIGURATIVI}') ON CONFLICT (codice) DO NOTHING"
    )
    op.execute(
        "INSERT INTO voci_rendiconto (codice, descrizione, sezione_codice) "
        f"VALUES (15, '{_COSTI_FIGURATIVI}', 4) ON CONFLICT (codice) DO NOTHING"
    )

    # 5. Vincola sezione_codice a NOT NULL ora che ogni riga è popolata.
    op.alter_column("voci_rendiconto", "sezione_codice", nullable=False)

    # 6. Tabella ponte N:M voce↔sottovoce.
    op.create_table(
        "voci_sottovoci_rendiconto",
        sa.Column("voce_codice", sa.SmallInteger(), nullable=False),
        sa.Column("sottovoce_codice", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["voce_codice"], ["voci_rendiconto.codice"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["sottovoce_codice"], ["sottovoci_rendiconto.codice"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("voce_codice", "sottovoce_codice"),
    )

    # 7. Popola la tabella ponte. Il JOIN sui lookup ignora le coppie i cui
    #    codici non esistono (DB appena migrato senza seed).
    pairs = [(v, s) for v, subs in _JUNCTION.items() for s in subs]
    values = ", ".join(f"({v}, {s})" for v, s in pairs)
    op.execute(
        f"""
        INSERT INTO voci_sottovoci_rendiconto (voce_codice, sottovoce_codice)
        SELECT t.v, t.s
        FROM (VALUES {values}) AS t(v, s)
        JOIN voci_rendiconto vr ON vr.codice = t.v
        JOIN sottovoci_rendiconto sv ON sv.codice = t.s
        """
    )


def downgrade() -> None:
    op.drop_table("voci_sottovoci_rendiconto")

    # Rimuove la voce/sezione "Costi e proventi figurativi".
    op.execute("DELETE FROM voci_rendiconto WHERE codice = 15")
    op.execute("DELETE FROM sezioni_rendiconto WHERE codice = 4")

    op.drop_column("voci_rendiconto", "sezione_codice")

    # Ripristina la voce 7 (doppione). La riassegnazione 7→5 delle voci di
    # contabilità è una fusione di dati e NON è reversibile: le righe già
    # spostate restano sulla voce 5.
    op.execute(
        "INSERT INTO voci_rendiconto (codice, descrizione) "
        f"VALUES (7, '{_VOCE_7_DESCRIZIONE}') ON CONFLICT (codice) DO NOTHING"
    )
