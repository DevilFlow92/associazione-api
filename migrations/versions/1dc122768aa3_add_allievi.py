"""add_allievi

Revision ID: 1dc122768aa3
Revises: b8e4d1c6f0a3
Create Date: 2026-07-31 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1dc122768aa3"
down_revision: str | Sequence[str] | None = "b8e4d1c6f0a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "allievi",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codice_allievo", sa.String(length=5), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.Column("indirizzo_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["indirizzo_id"], ["indirizzi.id"]),
        sa.ForeignKeyConstraint(["persona_id"], ["persone.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("persona_id", name="uq_allievi_persona_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("allievi")
