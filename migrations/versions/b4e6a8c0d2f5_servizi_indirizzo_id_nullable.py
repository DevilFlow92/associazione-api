"""servizi indirizzo_id nullable

Allinea ``Servizio`` a ``Prova`` rendendo ``servizi.indirizzo_id`` nullable:
un servizio può essere organizzato rapidamente (es. una richiesta al volo)
senza che il luogo sia ancora stato deciso, con l'indirizzo confermato in un
secondo momento.

Il vincolo viene solo allentato, quindi non c'è nessun dato da migrare in
upgrade. Il downgrade ristringe il vincolo e fallisce, di proposito, se nel
frattempo sono stati creati servizi senza indirizzo (vedi ``downgrade``).

Revision ID: b4e6a8c0d2f5
Revises: ca74763d4531
Create Date: 2026-07-26 15:12:03.417220

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4e6a8c0d2f5"
down_revision: str | Sequence[str] | None = "ca74763d4531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "servizi",
        "indirizzo_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema.

    Nessuna bonifica automatica dei dati: se esistono servizi con
    ``indirizzo_id`` nullo l'``ALTER`` fallisce ed è l'operatore a decidere
    come risolverli (assegnare un indirizzo o cancellarli). Cancellarli qui
    significherebbe rimuovere in cascata anche presenze, repertorio e
    ricevute collegate, una perdita di dati silenziosa in un downgrade.
    """
    op.alter_column(
        "servizi",
        "indirizzo_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
