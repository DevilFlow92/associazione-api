"""pass 2b — contabilità (voci contabilità, flussi cassa, rendiconto lookups)

Tabelle dimensione del rendiconto (SezioneRendiconto, VoceRendiconto,
SottovoceRendiconto, NaturaFlusso), le voci di contabilità (S_VoceContabilita)
e i movimenti di cassa (T_FlussoCassa).

Revision ID: c5f8b1a2e9d3
Revises: a3e7c2d18f40
Create Date: 2026-06-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5f8b1a2e9d3"
down_revision: str | Sequence[str] | None = "a3e7c2d18f40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # ── Tabelle dimensione del rendiconto ────────────────────────────────────
    op.create_table(
        "sezioni_rendiconto",
        sa.Column("codice", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("descrizione", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("codice"),
    )
    op.create_table(
        "voci_rendiconto",
        sa.Column("codice", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("descrizione", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("codice"),
    )
    op.create_table(
        "sottovoci_rendiconto",
        sa.Column("codice", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("descrizione", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("codice"),
    )
    op.create_table(
        "nature_flusso",
        sa.Column("codice", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("descrizione", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("codice"),
    )

    # ── Voci di contabilità (S_VoceContabilita) ──────────────────────────────
    op.create_table(
        "voci_contabilita",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("banda_codice", sa.SmallInteger(), nullable=False),
        sa.Column("voce_contabilita", sa.String(length=100), nullable=False),
        sa.Column("sezione_rendiconto_codice", sa.SmallInteger(), nullable=False),
        sa.Column("voce_rendiconto_codice", sa.SmallInteger(), nullable=False),
        sa.Column("sottovoce_rendiconto_codice", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(["banda_codice"], ["bande.codice"]),
        sa.ForeignKeyConstraint(
            ["sezione_rendiconto_codice"], ["sezioni_rendiconto.codice"]
        ),
        sa.ForeignKeyConstraint(
            ["sottovoce_rendiconto_codice"], ["sottovoci_rendiconto.codice"]
        ),
        sa.ForeignKeyConstraint(["voce_rendiconto_codice"], ["voci_rendiconto.codice"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── Movimenti di cassa (T_FlussoCassa) ───────────────────────────────────
    op.create_table(
        "flussi_cassa",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data_registrazione", sa.DateTime(), nullable=False),
        sa.Column("descrizione_operazione", sa.String(length=255), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("voce_contabilita_id", sa.Integer(), nullable=False),
        sa.Column("importo", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("segno", sa.String(length=5), nullable=False),
        sa.Column("natura_flusso_codice", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(["natura_flusso_codice"], ["nature_flusso.codice"]),
        sa.ForeignKeyConstraint(["voce_contabilita_id"], ["voci_contabilita.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("flussi_cassa")
    op.drop_table("voci_contabilita")
    op.drop_table("nature_flusso")
    op.drop_table("sottovoci_rendiconto")
    op.drop_table("voci_rendiconto")
    op.drop_table("sezioni_rendiconto")
