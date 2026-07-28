"""corsi musicali — tipi_corso, corsi, permessi corsi:read/write

Prima card della Fase 3 del backlog Attività. Introduce la lookup
``tipi_corso`` (ottoni, percussioni, ance, pianoforte) e l'entità ``corsi``
(contenitore di un corso musicale della banda per un dato anno, con
coordinatore e insegnante opzionali).

``coordinatore_persona_id``/``insegnante_persona_id`` referenziano
``persone.id`` (non ``soci.id``), coerente con la generalizzazione già
adottata da ``Ricevuta.persona_id``: un insegnante può essere un esterno
pagato, non necessariamente un socio.

Nessun vincolo di unicità su (tipo_corso_codice, anno, banda_codice): corsi
paralleli dello stesso tipo nello stesso anno (livelli diversi, insegnanti
diversi) sono ammessi nel dominio.

Seed: 4 valori di ``tipi_corso`` (ottoni, percussioni, ance, pianoforte) e
catalogo permessi ``corsi:read``/``corsi:write``, assegnati ai ruoli di
gestione principali (1 superuser, 2 Presidente, 3 Tesoriere, 4 Segretario,
5 Vice Presidente), stesso schema già in uso per ``templates:read/write``.

Revision ID: f7a2c9e4b6d1
Revises: b4e6a8c0d2f5
Create Date: 2026-07-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7a2c9e4b6d1"
down_revision: str | Sequence[str] | None = "b4e6a8c0d2f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CORSI_RUOLI_PERMESSI = {
    1: ["corsi:read", "corsi:write"],
    2: ["corsi:read", "corsi:write"],
    3: ["corsi:read", "corsi:write"],
    4: ["corsi:read", "corsi:write"],
    5: ["corsi:read", "corsi:write"],
}


def upgrade() -> None:
    op.create_table(
        "tipi_corso",
        sa.Column("codice", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("descrizione", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("codice"),
    )

    op.create_table(
        "corsi",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("banda_codice", sa.SmallInteger(), nullable=False),
        sa.Column("tipo_corso_codice", sa.SmallInteger(), nullable=False),
        sa.Column("anno", sa.Integer(), nullable=False),
        sa.Column("coordinatore_persona_id", sa.Integer(), nullable=True),
        sa.Column("insegnante_persona_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["banda_codice"], ["bande.codice"]),
        sa.ForeignKeyConstraint(["tipo_corso_codice"], ["tipi_corso.codice"]),
        sa.ForeignKeyConstraint(["coordinatore_persona_id"], ["persone.id"]),
        sa.ForeignKeyConstraint(["insegnante_persona_id"], ["persone.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        """
        INSERT INTO tipi_corso (codice, descrizione) VALUES
            (1, 'Ottoni'),
            (2, 'Percussioni'),
            (3, 'Ance'),
            (4, 'Pianoforte')
        ON CONFLICT (codice) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO permessi (codice, descrizione) VALUES
            ('corsi:read',  'Visualizzare i corsi musicali'),
            ('corsi:write', 'Gestire i corsi musicali')
        ON CONFLICT (codice) DO NOTHING
        """
    )

    bind = op.get_bind()
    for ruolo_id, permessi in CORSI_RUOLI_PERMESSI.items():
        for codice in permessi:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO ruoli_permessi (ruolo_id, permesso_codice)
                    VALUES (:rid, :cod)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"rid": ruolo_id, "cod": codice},
            )


def downgrade() -> None:
    bind = op.get_bind()
    for ruolo_id, permessi in CORSI_RUOLI_PERMESSI.items():
        for codice in permessi:
            bind.execute(
                sa.text(
                    """
                    DELETE FROM ruoli_permessi
                    WHERE ruolo_id = :rid AND permesso_codice = :cod
                    """
                ),
                {"rid": ruolo_id, "cod": codice},
            )

    op.execute(
        """
        DELETE FROM permessi WHERE codice IN (
            'corsi:read',
            'corsi:write'
        )
        """
    )

    op.drop_table("corsi")
    op.drop_table("tipi_corso")
