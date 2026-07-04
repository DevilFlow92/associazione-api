"""assegna templates:read/write ai ruoli di gestione principali

Assegna i permessi ``templates:read`` e ``templates:write`` ai ruoli:
- 1 (superuser) — per completezza, bypassa sempre il controllo, ma esplicito
- 2 (Presidente)
- 3 (Tesoriere)
- 4 (Segretario)
- 5 (Vice Presidente)

Questi ruoli hanno il diritto di leggere/gestire i template di modulistica.
Non viene toccato il ruolo 6 (Consigliere), 7 (Socio Sostenitore), 8
(Socio Bandista) — resta traccia della scelta in questa migration.

Revision ID: 8b833e91a3b6
Revises: 54cecb82dfc0
Create Date: 2026-07-04 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8b833e91a3b6"
down_revision: str | Sequence[str] | None = "54cecb82dfc0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TEMPLATES_RUOLI_PERMESSI = {
    1: ["templates:read", "templates:write"],
    2: ["templates:read", "templates:write"],
    3: ["templates:read", "templates:write"],
    4: ["templates:read", "templates:write"],
    5: ["templates:read", "templates:write"],
}


def upgrade() -> None:
    bind = op.get_bind()

    for ruolo_id, permessi in TEMPLATES_RUOLI_PERMESSI.items():
        for codice in permessi:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO ruoli_permessi (ruolo_id, permesso_codice)
                    VALUES (:rid, :cod)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"rid": ruolo_id, "cod": codice},
            )


def downgrade() -> None:
    bind = op.get_bind()

    for ruolo_id, permessi in TEMPLATES_RUOLI_PERMESSI.items():
        for codice in permessi:
            bind.execute(
                sa.text(
                    """
                    DELETE FROM ruoli_permessi
                    WHERE ruolo_id = :rid AND permesso_codice = :cod
                    """
                ),
                {"rid": ruolo_id, "cod": codice},
            )
