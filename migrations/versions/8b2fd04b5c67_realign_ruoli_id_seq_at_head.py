"""riallinea ruoli_id_seq al MAX(id) reale

e3b39b83930c ha corretto la sequence subito dopo il seed del ruolo
``superuser`` (id=1), ma la migration successiva a1b2c3d4e5f6 inserisce a
sua volta i ruoli di default con id espliciti (2-8, tramite
``INSERT ... ON CONFLICT (id) DO UPDATE``), bypassando di nuovo la
sequence senza fare setval. Il risultato è che ``ruoli_id_seq`` resta
allineata a 2 (valore lasciato da e3b39b83930c) mentre il MAX(id) reale in
tabella arriva a 8: il prossimo INSERT di un nuovo ruolo senza id esplicito
(es. da applicazione, non da migration) rigenererebbe id=2 e fallirebbe con
UniqueViolation.

Questa migration gira in coda alla catena attuale (dopo tutte le
migration che seedano ``ruoli`` con id espliciti) e riallinea la sequence
al vero MAX(id), così da coprire sia i DB nati da zero sia quelli
esistenti la cui sequence fosse già disallineata per lo stesso motivo.

Revision ID: 8b2fd04b5c67
Revises: 1dc122768aa3
Create Date: 2026-08-22 00:00:00.000001

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8b2fd04b5c67"
down_revision: str | Sequence[str] | None = "1dc122768aa3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "SELECT setval('ruoli_id_seq', COALESCE((SELECT MAX(id) FROM ruoli), 1))"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # No-op: vedi e3b39b83930c per la motivazione.
    pass
