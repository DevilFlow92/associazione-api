"""expand comuni.codice_catastale to 6 chars

Revision ID: 9986a7c1f2b3
Revises: b7c1d9e2f3a4
Create Date: 2026-06-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9986a7c1f2b3"
down_revision = "b7c1d9e2f3a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "comuni",
        "codice_catastale",
        type_=sa.String(length=6),
        existing_type=sa.String(length=5),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "comuni",
        "codice_catastale",
        type_=sa.String(length=5),
        existing_type=sa.String(length=6),
        existing_nullable=True,
    )
