"""create templates table with timezone

Revision ID: c3f0b0575da1
Revises: 607353a49669
Create Date: 2026-06-07 08:33:02.814588

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3f0b0575da1"
down_revision: str | Sequence[str] | None = "607353a49669"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("descrizione", sa.String(length=500), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("dimensione_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("attivo", sa.Boolean(), nullable=False),
        sa.Column("creato_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column("aggiornato_il", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("templates")
