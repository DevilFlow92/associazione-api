"""voci repertorio table

Introduce ``RepertorioItem`` (tabella ``voci_repertorio``), primo
collegamento tra ``Servizio`` e le composizioni (``NomeParte``) che ne
compongono il programma, con un ordine esplicito. È il primo passo verso il
libretto PDF: la card successiva selezionerà gli ``Spartito`` corrispondenti
incrociando queste voci con l'organico del servizio.

``servizio_id`` è nullable in previsione delle fasi successive del backlog
Attività (``prova_id``), ma per ora deve essere sempre valorizzato: il CHECK
``ck_repertorio_item_servizio_id_required`` lo impone finché quella fase non
arriva.

Revision ID: 74e4f7c2a1dc
Revises: 5fb732d2a6c2
Create Date: 2026-07-19 19:21:37.178320

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "74e4f7c2a1dc"
down_revision: str | Sequence[str] | None = "5fb732d2a6c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "voci_repertorio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome_parte_id", sa.Integer(), nullable=False),
        sa.Column("servizio_id", sa.Integer(), nullable=True),
        sa.Column("ordine", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.CheckConstraint(
            "servizio_id IS NOT NULL", name="ck_repertorio_item_servizio_id_required"
        ),
        sa.ForeignKeyConstraint(["nome_parte_id"], ["nome_parti.id"]),
        sa.ForeignKeyConstraint(["servizio_id"], ["servizi.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "nome_parte_id",
            "servizio_id",
            name="uq_repertorio_item_nome_parte_servizio",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("voci_repertorio")
