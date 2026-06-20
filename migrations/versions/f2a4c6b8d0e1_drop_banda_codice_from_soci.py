"""drop banda_codice from soci, band derives from persona

Revision ID: f2a4c6b8d0e1
Revises: 4185ab91d4eb
Create Date: 2026-06-19 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f2a4c6b8d0e1"
down_revision: str | Sequence[str] | None = "4185ab91d4eb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("soci_banda_codice_fkey", "soci", type_="foreignkey")
    op.drop_column("soci", "banda_codice")


def downgrade() -> None:
    """Downgrade schema."""
    # Reintroduce la colonna come nullable, ribackfilla la banda dalla persona
    # collegata (la banda deriva da ``persone.banda_codice``) e solo allora
    # ripristina il vincolo NOT NULL e la foreign key originali.
    op.add_column("soci", sa.Column("banda_codice", sa.SmallInteger(), nullable=True))
    op.execute(
        "UPDATE soci SET banda_codice = persone.banda_codice "
        "FROM persone WHERE soci.persona_id = persone.id"
    )
    op.alter_column("soci", "banda_codice", nullable=False)
    op.create_foreign_key(
        "soci_banda_codice_fkey", "soci", "bande", ["banda_codice"], ["codice"]
    )
