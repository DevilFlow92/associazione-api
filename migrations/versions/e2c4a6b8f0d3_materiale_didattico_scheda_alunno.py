"""materiale didattico allegato alla scheda alunno

Card #217. Introduce ``scheda_alunno_materiali``: file caricati su storage o
link esterni allegati a una scheda alunno. Arco esclusivo tra
``storage_key`` (valorizzato solo per i materiali di tipo file) e ``url``
(solo per i link) tramite CHECK, stesso linguaggio SQL già in uso per l'arco
di ``Presenza`` (``ck_presenza_arc_servizio_prova_lezione``): niente cast a
intero, per restare portabile su SQLite.

Nessuno storico (a differenza di ``scheda_alunno_voci_storico``): la
cancellazione di un materiale è un hard delete, non c'è uno stato da
preservare nel tempo.

Revision ID: e2c4a6b8f0d3
Revises: d3f5a7b9c1e4
Create Date: 2026-08-24 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e2c4a6b8f0d3"
down_revision: str | Sequence[str] | None = "d3f5a7b9c1e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ARC_ESCLUSIVO_STORAGE_KEY_URL = (
    "(storage_key IS NOT NULL AND url IS NULL) OR "
    "(storage_key IS NULL AND url IS NOT NULL)"
)


def upgrade() -> None:
    op.create_table(
        "scheda_alunno_materiali",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scheda_alunno_id", sa.Integer(), nullable=False),
        sa.Column("titolo", sa.String(length=200), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("nome_file_originale", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("dimensione_bytes", sa.Integer(), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("caricato_da_persona_id", sa.Integer(), nullable=True),
        sa.Column(
            "data_caricamento",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["scheda_alunno_id"], ["schede_alunno.id"]),
        sa.ForeignKeyConstraint(["caricato_da_persona_id"], ["persone.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_check_constraint(
        "ck_scheda_alunno_materiale_arc_storage_key_url",
        "scheda_alunno_materiali",
        _ARC_ESCLUSIVO_STORAGE_KEY_URL,
    )


def downgrade() -> None:
    op.drop_table("scheda_alunno_materiali")
