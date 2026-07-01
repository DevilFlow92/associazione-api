"""spartiti — introduce NomeParte (two-level model)

Introduce a two-level model for the sheet-music archive:

  NomeParte (the composition / title)
    └── Spartito  (one physical file / instrumental part per row)

Previously ``spartiti`` held all metadata directly (including the link to a
``Documento``).  After this migration each ``Spartito`` belongs to a
``NomeParte`` which carries the identifying information (nome, tipo_spartito,
banda).  A single ``NomeParte`` can have multiple ``Spartiti`` (e.g. one PDF
per instrument).

DATA PRESERVATION STRATEGY
For every existing ``spartito`` row the migration creates one ``nome_parte``,
deriving the name from the linked documento (file extension stripped).
``documento_id`` is then made nullable so that a ``Spartito`` can exist before
a PDF is attached.  Because the mapping from one spartito to one nome_parte is
1-to-1 during the backfill, the correlated-subquery approach (ORDER BY id,
LIMIT 1) is used so that rows that share the same tipo+banda are handled
safely.

DOWNGRADE IS LOSSY: ``nome_parti`` is dropped and ``nome_parte_id`` is
removed; any ``spartiti`` rows that were created after this migration (i.e.
those whose ``documento_id`` is NULL) will violate the NOT NULL constraint
re-added on downgrade and must be cleaned up manually beforehand.

Revision ID: e3c1a7f5b9d2
Revises: b1d3e5f7a9c2
Create Date: 2026-07-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3c1a7f5b9d2"
down_revision: str | Sequence[str] | None = "b1d3e5f7a9c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # ── 1. Create nome_parti ──────────────────────────────────────────────────
    op.create_table(
        "nome_parti",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("tipo_spartito_codice", sa.SmallInteger(), nullable=False),
        sa.Column("banda_codice", sa.SmallInteger(), nullable=False),
        sa.Column("url_riferimento", sa.String(length=500), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(
            ["tipo_spartito_codice"],
            ["tipi_spartito.codice"],
            name="fk_nome_parti_tipo_spartito_codice",
        ),
        sa.ForeignKeyConstraint(
            ["banda_codice"],
            ["bande.codice"],
            name="fk_nome_parti_banda_codice",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── 2. Add nome_parte_id to spartiti (nullable for backfill) ──────────────
    op.add_column(
        "spartiti",
        sa.Column("nome_parte_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_spartiti_nome_parte_id",
        "spartiti",
        "nome_parti",
        ["nome_parte_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── 3. Make documento_id nullable on spartiti ─────────────────────────────
    op.alter_column(
        "spartiti", "documento_id", existing_type=sa.Integer(), nullable=True
    )

    # ── 4. Data preservation ──────────────────────────────────────────────────
    # 4a. One nome_parte per existing spartito, name derived from documento.
    op.execute(
        """
        INSERT INTO nome_parti (nome, tipo_spartito_codice, banda_codice)
        SELECT
            REGEXP_REPLACE(d.nome, '\\.[^.]+$', ''),
            s.tipo_spartito_codice,
            s.banda_codice
        FROM spartiti s
        JOIN documenti d ON d.id = s.documento_id
        """
    )

    # 4b. Link each spartito to its newly created nome_parte.
    #     Correlated subquery (ORDER BY id, LIMIT 1) handles duplicate
    #     tipo+banda combinations safely.
    op.execute(
        """
        UPDATE spartiti
        SET nome_parte_id = (
            SELECT np.id FROM nome_parti np
            WHERE np.tipo_spartito_codice = spartiti.tipo_spartito_codice
              AND np.banda_codice = spartiti.banda_codice
            ORDER BY np.id
            LIMIT 1
        )
        WHERE nome_parte_id IS NULL
        """
    )

    # ── 5. nome_parte_id is now populated — enforce NOT NULL ──────────────────
    op.alter_column(
        "spartiti", "nome_parte_id", existing_type=sa.Integer(), nullable=False
    )


def downgrade() -> None:
    """Downgrade schema.

    LOSSY: ``nome_parti`` is dropped entirely.  Any ``spartiti`` rows whose
    ``documento_id`` is NULL (created after this migration) will violate the
    NOT NULL constraint re-added here — delete or fix those rows manually
    before running this downgrade.
    """
    # Drop FK and column added by this migration.
    op.drop_constraint("fk_spartiti_nome_parte_id", "spartiti", type_="foreignkey")
    op.drop_column("spartiti", "nome_parte_id")

    # Restore documento_id as NOT NULL.
    # WARNING: rows with NULL documento_id must be cleaned up first.
    op.alter_column(
        "spartiti", "documento_id", existing_type=sa.Integer(), nullable=False
    )

    op.drop_table("nome_parti")
