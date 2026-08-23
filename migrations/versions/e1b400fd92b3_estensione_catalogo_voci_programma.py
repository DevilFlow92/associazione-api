"""estensione catalogo voci programma — categorie, livello

Introduce la lookup ``categorie_voce_programma`` (tecnica, scale, repertorio,
teoria, ...) e sostituisce la colonna libera ``categoria`` (String) di
``voci_programma_catalogo`` con ``categoria_codice`` (FK verso la nuova
lookup), aggiungendo anche ``livello`` (progressione tecnica di una voce
all'interno della sua categoria).

La tabella ``voci_programma_catalogo`` non è mai stata popolata in
produzione (introdotta da ``5c56e2f36737`` sullo stesso rilascio): DROP/ADD
diretti sulla colonna, nessuna conversione di dati necessaria.

Il vincolo UNIQUE ``uq_voci_programma_catalogo_tipo_corso_testo`` resta
invariato: categoria e livello non ne fanno parte.

Revision ID: e1b400fd92b3
Revises: 5c56e2f36737
Create Date: 2026-08-23 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e1b400fd92b3"
down_revision: str | Sequence[str] | None = "5c56e2f36737"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categorie_voce_programma",
        sa.Column("codice", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("descrizione", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("codice"),
    )

    op.drop_column("voci_programma_catalogo", "categoria")
    op.add_column(
        "voci_programma_catalogo",
        sa.Column("categoria_codice", sa.SmallInteger(), nullable=False),
    )
    op.add_column(
        "voci_programma_catalogo",
        sa.Column("livello", sa.SmallInteger(), nullable=False, server_default="1"),
    )
    op.create_foreign_key(
        "fk_voci_programma_catalogo_categoria_codice",
        "voci_programma_catalogo",
        "categorie_voce_programma",
        ["categoria_codice"],
        ["codice"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_voci_programma_catalogo_categoria_codice",
        "voci_programma_catalogo",
        type_="foreignkey",
    )
    op.drop_column("voci_programma_catalogo", "livello")
    op.drop_column("voci_programma_catalogo", "categoria_codice")
    op.add_column(
        "voci_programma_catalogo",
        sa.Column("categoria", sa.String(length=50), nullable=False),
    )

    op.drop_table("categorie_voce_programma")
