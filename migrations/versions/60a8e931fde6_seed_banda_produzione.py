"""seed banda di produzione

Nessuna migration precedente inserisce mai una riga in ``bande``: la
tabella viene creata da b7c1d9e2f3a4_apply_domain_model_anagrafica.py ma
popolata solo da scripts/seed_production.py (funzione
``seed_lookups_pass1``), uno script eseguito manualmente e non collegato
alla catena di migration. Su un DB nato da zero via solo
``alembic upgrade head`` (senza eseguire quello script), la tabella
``bande`` resta vuota, e b2c3d4e5f6a1_seed_piano_dei_conti.py fallisce con
ForeignKeyViolation perché assume ``banda_codice=1`` già esistente
("unica banda in produzione").

Questa migration si inserisce subito prima di b2c3d4e5f6a1 nella catena
(il suo ``down_revision`` è stato aggiornato per puntare qui), così la
riga esiste già quando b2c3d4e5f6a1 gira. Non tocca il contenuto/revision
id di a1b2c3d4e5f6 né di b2c3d4e5f6a1, entrambe già applicate in
produzione: per i DB che hanno già superato b2c3d4e5f6a1 nella loro
storia, alembic non rigioca questa revision (è "a monte" della revision
corrente), quindi l'inserimento è innocuo.

Descrizione e codice presi da scripts/seed_production.py (stessa riga
seedata lì), non inventati.

Revision ID: 60a8e931fde6
Revises: a1b2c3d4e5f6
Create Date: 2026-08-22 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "60a8e931fde6"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO bande (codice, descrizione) VALUES (:c, :d) "
            "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione"
        ),
        {
            "c": 1,
            "d": 'Associazione Musicale "S. Antonio" Banda Musicale Città di Quartu',
        },
    )


def downgrade() -> None:
    """Downgrade schema."""
    # No-op: b2c3d4e5f6a1 (a valle) referenzia banda_codice=1 tramite FK;
    # rimuovere la riga qui romperebbe il downgrade della migration
    # successiva prima che questa venga eseguita.
    pass
