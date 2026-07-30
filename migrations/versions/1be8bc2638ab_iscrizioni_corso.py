"""iscrizioni corso — stati_iscrizione_corso, iscrizioni_corso

Terza card della Fase 3 del backlog Attività. Introduce l'iscrizione di una
Persona (l'alunno) a un Corso musicale specifico. Concetto distinto
dall'``Iscrizione`` esistente (adesione annuale di un Socio alla banda,
tabella ``iscrizioni``): qui l'iscritto è una Persona qualunque, non
necessariamente un Socio, coerente con la generalizzazione già adottata da
``Corso.coordinatore_persona_id``/``insegnante_persona_id``.

Nuova lookup dedicata ``stati_iscrizione_corso`` invece di riusare
``stati_iscrizione``: quest'ultima è accoppiata alla logica di quota annuale
socio (``IscrizioneService._is_pagata`` innesca un FlussoCassa automatico sul
valore "Pagata"), semantica che non si applica a un'iscrizione a un corso.
Seed: Richiesta, Confermata, Annullata, Completata.

Nessun vincolo di unicità su (persona_id, corso_id): una persona può essere
re-iscritta allo stesso corso dopo un'iscrizione annullata.

``documento_id`` nullable: il modulo di richiesta potrebbe non essere ancora
stato caricato al momento della creazione dell'iscrizione.

Permessi: riusa ``corsi:read``/``corsi:write`` (già assegnati ai ruoli di
gestione da f7a2c9e4b6d1), essendo l'iscrizione scoped a un Corso.

Revision ID: 1be8bc2638ab
Revises: c8e3f1a9b5d7
Create Date: 2026-07-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1be8bc2638ab"
down_revision: str | Sequence[str] | None = "c8e3f1a9b5d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stati_iscrizione_corso",
        sa.Column("codice", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("descrizione", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("codice"),
    )

    op.execute(
        """
        INSERT INTO stati_iscrizione_corso (codice, descrizione) VALUES
            (1, 'Richiesta'),
            (2, 'Confermata'),
            (3, 'Annullata'),
            (4, 'Completata')
        ON CONFLICT (codice) DO NOTHING
        """
    )

    op.create_table(
        "iscrizioni_corso",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("corso_id", sa.Integer(), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.Column("stato_iscrizione_corso_codice", sa.SmallInteger(), nullable=False),
        sa.Column("documento_id", sa.Integer(), nullable=True),
        sa.Column("data_iscrizione", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["corso_id"], ["corsi.id"]),
        sa.ForeignKeyConstraint(["persona_id"], ["persone.id"]),
        sa.ForeignKeyConstraint(
            ["stato_iscrizione_corso_codice"], ["stati_iscrizione_corso.codice"]
        ),
        sa.ForeignKeyConstraint(["documento_id"], ["documenti.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("iscrizioni_corso")
    op.drop_table("stati_iscrizione_corso")
