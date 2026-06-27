"""add iscrizioni:read and iscrizioni:write permissions

Revision ID: 7a8b9c0d1e2f
Revises: 5d29d2a49788
Create Date: 2026-06-27 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a8b9c0d1e2f"
down_revision: str | Sequence[str] | None = "5d29d2a49788"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.bulk_insert(
        sa.table(
            "permessi",
            sa.column("codice", sa.String),
            sa.column("descrizione", sa.String),
        ),
        [
            {"codice": "iscrizioni:read", "descrizione": "Visualizzare iscrizioni"},
            {"codice": "iscrizioni:write", "descrizione": "Gestire iscrizioni"},
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM permessi WHERE codice IN "
        "('iscrizioni:read', 'iscrizioni:write')"
    )
