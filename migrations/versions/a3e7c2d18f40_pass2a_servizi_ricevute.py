"""pass 2a — servizi, ricevute, banda↔indirizzo

Eventi (T_Servizi), ricevute (T_Ricevute) e la relazione molti-a-molti
banda↔indirizzo (T_R_Banda_Indirizzo).

Revision ID: a3e7c2d18f40
Revises: 9986a7c1f2b3
Create Date: 2026-06-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3e7c2d18f40"
down_revision: str | Sequence[str] | None = "9986a7c1f2b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "servizi",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("banda_codice", sa.SmallInteger(), nullable=False),
        sa.Column("anno", sa.Integer(), nullable=False),
        sa.Column("descrizione_servizio", sa.String(length=255), nullable=False),
        sa.Column("data_servizio", sa.DateTime(), nullable=False),
        sa.Column("indirizzo_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["banda_codice"], ["bande.codice"]),
        sa.ForeignKeyConstraint(["indirizzo_id"], ["indirizzi.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ricevute",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("servizio_id", sa.Integer(), nullable=False),
        sa.Column("esterno_id", sa.Integer(), nullable=False),
        sa.Column("data_ricevuta", sa.DateTime(), nullable=False),
        sa.Column("importo", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("note_in_stampa", sa.String(length=255), nullable=True),
        sa.Column("note_fuori_stampa", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["esterno_id"], ["esterni.id"]),
        sa.ForeignKeyConstraint(["servizio_id"], ["servizi.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "bande_indirizzi",
        sa.Column("banda_codice", sa.SmallInteger(), nullable=False),
        sa.Column("indirizzo_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["banda_codice"], ["bande.codice"]),
        sa.ForeignKeyConstraint(["indirizzo_id"], ["indirizzi.id"]),
        sa.PrimaryKeyConstraint("banda_codice", "indirizzo_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("bande_indirizzi")
    op.drop_table("ricevute")
    op.drop_table("servizi")
