"""voci di programma sulla scheda alunno

Sostituisce il campo testuale libero ``programma`` di ``schede_alunno`` con
voci strutturate: ogni voce riferisce una ``VoceProgrammaCatalogo`` e porta
uno stato di avanzamento (``da_iniziare``/``in_corso``/``acquisita``), un
dettaglio libero opzionale e un ordine didattico scelto dall'insegnante.

Nessun vincolo UNIQUE su (scheda_alunno_id, voce_catalogo_id): la stessa
voce di catalogo può comparire più volte sulla stessa scheda con dettaglio
diverso (es. due passaggi diversi dello stesso studio).

``schede_alunno.programma`` non è mai stata popolata con contenuti
significativi in produzione (il beta tester è l'unico utente): DROP diretto
della colonna, nessuna strategia di migrazione dati.

Revision ID: 9f1e3d5c7b2a
Revises: f56e876f377b
Create Date: 2026-08-23 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9f1e3d5c7b2a"
down_revision: str | Sequence[str] | None = "f56e876f377b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scheda_alunno_voci",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scheda_alunno_id", sa.Integer(), nullable=False),
        sa.Column("voce_catalogo_id", sa.Integer(), nullable=False),
        sa.Column("stato", sa.String(length=20), nullable=False),
        sa.Column("dettaglio", sa.String(length=200), nullable=True),
        sa.Column("ordine", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(["scheda_alunno_id"], ["schede_alunno.id"]),
        sa.ForeignKeyConstraint(["voce_catalogo_id"], ["voci_programma_catalogo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.drop_column("schede_alunno", "programma")


def downgrade() -> None:
    op.add_column(
        "schede_alunno",
        sa.Column("programma", sa.Text(), nullable=True),
    )
    op.drop_table("scheda_alunno_voci")
