"""templates — FK opzionale verso sotto_cartelle

Aggiunge a ``templates`` la colonna ``sotto_cartella_id`` (Integer,
nullable, FK → sotto_cartelle.id, ondelete=SET NULL).

Relazione: un ``Template`` PUÒ essere associato a una ``SottoCartella``
dell'archivio documentale, usata per classificare i documenti generati
dal template (invece di lasciarli senza categoria). L'eliminazione della
sotto-cartella non invalida il template: il campo viene azzerato
(SET NULL) e il template torna allo stato «nessuna cartella».

Revision ID: d2f4a6b8c0e3
Revises: c4d6e8f0a1b3
Create Date: 2026-07-18 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d2f4a6b8c0e3"
down_revision: str | Sequence[str] | None = "c4d6e8f0a1b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "templates",
        sa.Column("sotto_cartella_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_templates_sotto_cartella_id",
        "templates",
        "sotto_cartelle",
        ["sotto_cartella_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_templates_sotto_cartella_id",
        "templates",
        type_="foreignkey",
    )
    op.drop_column("templates", "sotto_cartella_id")
