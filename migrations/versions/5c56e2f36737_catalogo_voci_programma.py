"""catalogo voci programma corsi

Introduce ``voci_programma_catalogo``: il catalogo di voci riutilizzabili
(scale, tecnica, repertorio, teoria, ...) da cui insegnante/coordinatore
compongono il programma di una scheda alunno, per tipo di corso.

Nessun nuovo permesso: la card riusa ``corsi:read``/``corsi:write`` già
seedati da ``f7a2c9e4b6d1``, coerente con il fatto che il catalogo è
materiale di gestione dei corsi, non una superficie distinta.

``attiva`` implementa soft-delete: una voce non si elimina mai fisicamente
(se creata per errore va disattivata e se ne crea una nuova), per non
invalidare riferimenti storici da schede alunno già compilate.

Revision ID: 5c56e2f36737
Revises: 8b2fd04b5c67
Create Date: 2026-08-23 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5c56e2f36737"
down_revision: str | Sequence[str] | None = "8b2fd04b5c67"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "voci_programma_catalogo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo_corso_codice", sa.SmallInteger(), nullable=False),
        sa.Column("categoria", sa.String(length=50), nullable=False),
        sa.Column("testo", sa.String(length=200), nullable=False),
        sa.Column("attiva", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["tipo_corso_codice"], ["tipi_corso.codice"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tipo_corso_codice",
            "testo",
            name="uq_voci_programma_catalogo_tipo_corso_testo",
        ),
    )


def downgrade() -> None:
    op.drop_table("voci_programma_catalogo")
