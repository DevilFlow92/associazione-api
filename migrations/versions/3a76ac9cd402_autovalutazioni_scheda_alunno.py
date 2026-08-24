"""autovalutazioni alunno sulla propria scheda

Card #218. Introduce ``scheda_alunno_autovalutazioni``: diario di
autovalutazione scritto dall'alunno stesso sulla propria scheda — primo caso
nel progetto di scrittura concessa all'alunno, non solo lettura, vedi
``assert_puo_scrivere_autovalutazione`` in ``app/services/rbac_row_level.py``.

``data_modifica`` è nullable e valorizzata solo se la voce viene editata dopo
la creazione, per distinguere "creata il" da "modificata l'ultima volta il"
nella UI — stesso principio già in uso altrove nel progetto (es.
``ConfigurazioneBandaAnno.data_chiusura``).

Revision ID: 3a76ac9cd402
Revises: e2c4a6b8f0d3
Create Date: 2026-08-24 10:04:29.455873
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3a76ac9cd402"
down_revision: str | Sequence[str] | None = "e2c4a6b8f0d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scheda_alunno_autovalutazioni",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scheda_alunno_id", sa.Integer(), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.Column("testo", sa.String(length=1000), nullable=False),
        sa.Column(
            "data_creazione",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("data_modifica", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["scheda_alunno_id"], ["schede_alunno.id"]),
        sa.ForeignKeyConstraint(["persona_id"], ["persone.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("scheda_alunno_autovalutazioni")
