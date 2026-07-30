"""lezione entita ed estensione arc esclusivo a 3 rami

Seconda card della Fase 3 del backlog Attività (Corsi Musicali). Introduce
``Lezione`` (tabella ``lezioni``): la singola sessione datata di un
``Corso`` (``corso_id`` obbligatoria — a differenza di Prova, una Lezione
appartiene sempre a un corso), con ``data_lezione`` (datetime unico, come
``Servizio.data_servizio``/``Prova.data_prova``) e ``indirizzo_id``
nullable (stesso discorso di Prova/Servizio dopo l'ultima card di
hardening: la sede può non essere ancora decisa).

Estende l'arc esclusivo su ``Presenza`` (introdotto in Fase 1, esteso a due
rami nella card #170 — Prova) da 2 a 3 rami: aggiunge ``lezione_id`` e
sostituisce il CHECK ``servizio_id``/``prova_id`` con uno che impone che
esattamente uno tra ``servizio_id``, ``prova_id`` e ``lezione_id`` sia
valorizzato. I 3 casi validi sono enumerati esplicitamente con AND/OR
(niente cast a intero, per restare portabile su SQLite come nella card
#170) per evitare ambiguità in una condizione più complessa della versione
a 2 rami.

``RepertorioItem``/``LibrettoService`` NON sono estesi a Lezione in questa
card: una lezione di corso non ha un "repertorio" nel senso di brani da
suonare in un programma (per decisione esplicita, confermata dal backlog
Fase 3 e non contraddetta dal codice).

Revision ID: c8e3f1a9b5d7
Revises: d5d0a91ceee4
Create Date: 2026-07-30 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8e3f1a9b5d7"
down_revision: str | Sequence[str] | None = "d5d0a91ceee4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ARC_ESCLUSIVO_SERVIZIO_PROVA_LEZIONE = (
    "(servizio_id IS NOT NULL AND prova_id IS NULL AND lezione_id IS NULL) OR "
    "(servizio_id IS NULL AND prova_id IS NOT NULL AND lezione_id IS NULL) OR "
    "(servizio_id IS NULL AND prova_id IS NULL AND lezione_id IS NOT NULL)"
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "lezioni",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("corso_id", sa.Integer(), nullable=False),
        sa.Column("data_lezione", sa.DateTime(), nullable=False),
        sa.Column("indirizzo_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["corso_id"], ["corsi.id"]),
        sa.ForeignKeyConstraint(["indirizzo_id"], ["indirizzi.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column("presenze", sa.Column("lezione_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_presenze_lezione_id_lezioni", "presenze", "lezioni", ["lezione_id"], ["id"]
    )
    op.create_unique_constraint(
        "uq_presenza_persona_lezione", "presenze", ["persona_id", "lezione_id"]
    )
    op.drop_constraint("ck_presenza_arc_servizio_prova", "presenze", type_="check")
    op.create_check_constraint(
        "ck_presenza_arc_servizio_prova_lezione",
        "presenze",
        _ARC_ESCLUSIVO_SERVIZIO_PROVA_LEZIONE,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_presenza_arc_servizio_prova_lezione", "presenze", type_="check"
    )
    op.create_check_constraint(
        "ck_presenza_arc_servizio_prova",
        "presenze",
        "(servizio_id IS NOT NULL AND prova_id IS NULL) OR "
        "(servizio_id IS NULL AND prova_id IS NOT NULL)",
    )
    op.drop_constraint("uq_presenza_persona_lezione", "presenze", type_="unique")
    op.drop_constraint("fk_presenze_lezione_id_lezioni", "presenze", type_="foreignkey")
    op.drop_column("presenze", "lezione_id")

    op.drop_table("lezioni")
