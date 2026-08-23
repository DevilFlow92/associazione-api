"""storico cambi di stato delle voci di programma

Introduce ``scheda_alunno_voci_storico``, append-only: una riga per la
creazione di ogni ``SchedaAlunnoVoce`` e una riga per ogni cambio di
``stato`` successivo (non per modifiche a ``dettaglio``/``ordine``, che non
sono transizioni di stato).

``scheda_alunno_id`` e ``voce_catalogo_id`` sono denormalizzati di proposito
(colonne semplici, non FK): la riga deve restare leggibile anche se la voce
o la scheda a cui si riferiva sono state cancellate. ``scheda_alunno_voce_id``
è invece una FK vera con ``ON DELETE SET NULL``: alla cancellazione della
voce la riga di storico sopravvive con il riferimento azzerato (il service
lo azzera esplicitamente anche a livello applicativo, per restare
indipendente dall'enforcement dei vincoli FK del database in uso — vedi
``SchedaAlunnoVoceStoricoRepository.azzera_riferimento_no_commit``).

Revision ID: b2d4f6a8c0e3
Revises: 9f1e3d5c7b2a
Create Date: 2026-08-23 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2d4f6a8c0e3"
down_revision: str | Sequence[str] | None = "9f1e3d5c7b2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scheda_alunno_voci_storico",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scheda_alunno_voce_id", sa.Integer(), nullable=True),
        sa.Column("scheda_alunno_id", sa.Integer(), nullable=False),
        sa.Column("voce_catalogo_id", sa.Integer(), nullable=False),
        sa.Column("stato_precedente", sa.String(length=20), nullable=True),
        sa.Column("stato_nuovo", sa.String(length=20), nullable=False),
        sa.Column("modificato_da_persona_id", sa.Integer(), nullable=True),
        sa.Column(
            "data_modifica",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["scheda_alunno_voce_id"],
            ["scheda_alunno_voci.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["modificato_da_persona_id"], ["persone.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("scheda_alunno_voci_storico")
