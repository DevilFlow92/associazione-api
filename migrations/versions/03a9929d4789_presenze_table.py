"""presenze table

Introduce ``Presenza``, primo collegamento tra ``Servizio`` e le persone
(soci ed esterni) che vi partecipano. Rappresenta sia la composizione
dell'organico (chi è chiamato a partecipare, ``stato`` nullo) sia lo stato
di presenza effettiva una volta tracciata.

``servizio_id`` è nullable in previsione delle fasi successive del backlog
Attività (``prova_id``, ``lezione_id``), ma per ora deve essere sempre
valorizzato: il CHECK ``ck_presenza_servizio_id_required`` lo impone
finché quelle fasi non arrivano.

Revision ID: 03a9929d4789
Revises: d2f4a6b8c0e3
Create Date: 2026-07-19 18:18:06.242683

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "03a9929d4789"
down_revision: str | Sequence[str] | None = "d2f4a6b8c0e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "presenze",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.Column("servizio_id", sa.Integer(), nullable=True),
        sa.Column(
            "stato",
            sa.Enum("PRESENTE", "ASSENTE", "GIUSTIFICATO", name="stato_presenza"),
            nullable=True,
        ),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.CheckConstraint(
            "servizio_id IS NOT NULL", name="ck_presenza_servizio_id_required"
        ),
        sa.ForeignKeyConstraint(["persona_id"], ["persone.id"]),
        sa.ForeignKeyConstraint(["servizio_id"], ["servizi.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "persona_id", "servizio_id", name="uq_presenza_persona_servizio"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("presenze")
    sa.Enum(name="stato_presenza").drop(op.get_bind(), checkfirst=True)
