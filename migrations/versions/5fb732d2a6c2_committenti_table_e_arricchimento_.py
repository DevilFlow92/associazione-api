"""committenti table e arricchimento servizio

Introduce ``Committente``, ente riutilizzabile tra più servizi (parrocchia,
comune, pro-loco, ...). Non è una ``Persona``: ha una ``denominazione``,
non un nominativo individuale.

Arricchisce ``servizi`` con tre colonne nullable:

- ``committente_id`` (FK opzionale → committenti.id, un servizio può non
  avere committente, es. un concerto proprio della banda);
- ``referente`` (nominativo di contatto specifico del singolo servizio,
  cambia anche a parità di committente);
- ``compenso_pattuito`` (importo concordato per il servizio).

Revision ID: 5fb732d2a6c2
Revises: 03a9929d4789
Create Date: 2026-07-19 19:03:29.897985

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5fb732d2a6c2"
down_revision: str | Sequence[str] | None = "03a9929d4789"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "committenti",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("denominazione", sa.String(length=255), nullable=False),
        sa.Column("indirizzo_id", sa.Integer(), nullable=True),
        sa.Column("codice_fiscale_piva", sa.String(length=50), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["indirizzo_id"], ["indirizzi.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("servizi", sa.Column("committente_id", sa.Integer(), nullable=True))
    op.add_column(
        "servizi", sa.Column("referente", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "servizi",
        sa.Column(
            "compenso_pattuito", sa.Numeric(precision=10, scale=2), nullable=True
        ),
    )
    op.create_foreign_key(
        "fk_servizi_committente_id",
        "servizi",
        "committenti",
        ["committente_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_servizi_committente_id", "servizi", type_="foreignkey")
    op.drop_column("servizi", "compenso_pattuito")
    op.drop_column("servizi", "referente")
    op.drop_column("servizi", "committente_id")
    op.drop_table("committenti")
