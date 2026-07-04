"""rebuild templates — documenti dinamici (modulistica)

Il vecchio modello ``Template`` legava un record a un ``Documento`` file
statico. Viene sostituito da un template documentale dinamico:
``contenuto_json`` (albero prodotto dall'editor TipTap) e
``entita_richieste`` (provider di merge field necessari a compilarlo).

Nessuna migrazione dati: il vecchio record va rimosso manualmente prima
del deploy.

Seed: catalogo permessi ``templates:read`` / ``templates:write``.

Revision ID: 54cecb82dfc0
Revises: f3b5d7e9a1c4
Create Date: 2026-07-04 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "54cecb82dfc0"
down_revision: str | Sequence[str] | None = "f3b5d7e9a1c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table("templates")

    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("descrizione", sa.String(length=500), nullable=True),
        sa.Column("contenuto_json", sa.JSON(), nullable=False),
        sa.Column("entita_richieste", sa.JSON(), nullable=False),
        sa.Column("creato_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column("aggiornato_il", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        """
        INSERT INTO permessi (codice, descrizione) VALUES
            ('templates:read',  'Visualizzare i template di modulistica'),
            ('templates:write', 'Gestire i template di modulistica')
        ON CONFLICT (codice) DO NOTHING
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        DELETE FROM permessi WHERE codice IN (
            'templates:read',
            'templates:write'
        )
        """
    )

    op.drop_table("templates")

    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("documento_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("descrizione", sa.String(length=500), nullable=True),
        sa.Column("creato_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column("aggiornato_il", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["documento_id"], ["documenti.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
