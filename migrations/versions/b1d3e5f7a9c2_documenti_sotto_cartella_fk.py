"""documenti — FK opzionale verso sotto_cartelle

Aggiunge a ``documenti`` la colonna ``sotto_cartella_id`` (Integer,
nullable, FK → sotto_cartelle.id, ondelete=SET NULL).

Relazione: un ``Documento`` PUÒ appartenere a una ``SottoCartella``, che a
sua volta appartiene a una ``MacroSezione``.  NULL significa «non
categorizzato nella struttura a due livelli» — il documento rimane
accessibile e filtrabile per ``tipo_documento_codice`` (asse di
classificazione ortogonale, pre-esistente, non toccato da questa
migrazione).  L'eliminazione di una sotto-cartella non rimuove i documenti
in essa contenuti: il campo viene azzerato (SET NULL) e i documenti tornano
allo stato «non categorizzato».

Revision ID: b1d3e5f7a9c2
Revises: a9b1c3d5e7f2
Create Date: 2026-06-30 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1d3e5f7a9c2"
down_revision: str | Sequence[str] | None = "a9b1c3d5e7f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "documenti",
        sa.Column("sotto_cartella_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_documenti_sotto_cartella_id",
        "documenti",
        "sotto_cartelle",
        ["sotto_cartella_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_documenti_sotto_cartella_id",
        "documenti",
        type_="foreignkey",
    )
    op.drop_column("documenti", "sotto_cartella_id")
