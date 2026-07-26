"""prova entita ed estensione arc esclusivo

Introduce ``Prova`` (tabella ``prove``): una prova musicale, orientata a un
``Servizio`` (``servizio_id`` valorizzato, in preparazione a un concerto) o
standalone (``servizio_id`` nullo).

Estende l'arc esclusivo introdotto in Fase 1 su ``Presenza`` e
``RepertorioItem`` (finora un placeholder a un solo ramo, come documentato
nelle migration 03a9929d4789 e 74e4f7c2a1dc): aggiunge ``prova_id`` a
entrambe le tabelle e sostituisce il CHECK ``... IS NOT NULL`` con un CHECK
che impone che esattamente uno tra ``servizio_id`` e ``prova_id`` sia
valorizzato. Il CHECK usa AND/OR anziché un cast a intero (es. ``::int``) per
restare portabile anche su SQLite, usato dalla suite di test.

Revision ID: ca74763d4531
Revises: d1a5c8f36b2e
Create Date: 2026-07-26 12:54:10.664551

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca74763d4531"
down_revision: str | Sequence[str] | None = "d1a5c8f36b2e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ARC_ESCLUSIVO_SERVIZIO_PROVA = (
    "(servizio_id IS NOT NULL AND prova_id IS NULL) OR "
    "(servizio_id IS NULL AND prova_id IS NOT NULL)"
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "prove",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("banda_codice", sa.SmallInteger(), nullable=False),
        sa.Column("data_prova", sa.DateTime(), nullable=False),
        sa.Column("indirizzo_id", sa.Integer(), nullable=True),
        sa.Column("servizio_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["banda_codice"], ["bande.codice"]),
        sa.ForeignKeyConstraint(["indirizzo_id"], ["indirizzi.id"]),
        sa.ForeignKeyConstraint(["servizio_id"], ["servizi.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column("presenze", sa.Column("prova_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_presenze_prova_id_prove", "presenze", "prove", ["prova_id"], ["id"]
    )
    op.create_unique_constraint(
        "uq_presenza_persona_prova", "presenze", ["persona_id", "prova_id"]
    )
    op.drop_constraint("ck_presenza_servizio_id_required", "presenze", type_="check")
    op.create_check_constraint(
        "ck_presenza_arc_servizio_prova", "presenze", _ARC_ESCLUSIVO_SERVIZIO_PROVA
    )

    op.add_column("voci_repertorio", sa.Column("prova_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_voci_repertorio_prova_id_prove",
        "voci_repertorio",
        "prove",
        ["prova_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_repertorio_item_nome_parte_prova",
        "voci_repertorio",
        ["nome_parte_id", "prova_id"],
    )
    op.drop_constraint(
        "ck_repertorio_item_servizio_id_required", "voci_repertorio", type_="check"
    )
    op.create_check_constraint(
        "ck_repertorio_item_arc_servizio_prova",
        "voci_repertorio",
        _ARC_ESCLUSIVO_SERVIZIO_PROVA,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_repertorio_item_arc_servizio_prova", "voci_repertorio", type_="check"
    )
    op.create_check_constraint(
        "ck_repertorio_item_servizio_id_required",
        "voci_repertorio",
        "servizio_id IS NOT NULL",
    )
    op.drop_constraint(
        "uq_repertorio_item_nome_parte_prova", "voci_repertorio", type_="unique"
    )
    op.drop_constraint(
        "fk_voci_repertorio_prova_id_prove", "voci_repertorio", type_="foreignkey"
    )
    op.drop_column("voci_repertorio", "prova_id")

    op.drop_constraint("ck_presenza_arc_servizio_prova", "presenze", type_="check")
    op.create_check_constraint(
        "ck_presenza_servizio_id_required", "presenze", "servizio_id IS NOT NULL"
    )
    op.drop_constraint("uq_presenza_persona_prova", "presenze", type_="unique")
    op.drop_constraint("fk_presenze_prova_id_prove", "presenze", type_="foreignkey")
    op.drop_column("presenze", "prova_id")

    op.drop_table("prove")
