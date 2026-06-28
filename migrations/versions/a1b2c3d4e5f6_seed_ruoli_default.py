"""Seed ruoli default associazione bandistica

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-06-28 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RUOLI = [
    (2, "Presidente", "Presidente dell'associazione"),
    (3, "Tesoriere", "Tesoriere dell'Associazione"),
    (4, "Segretario", "Segretario dell'Associazione"),
    (5, "Vice Presidente", "Vice Presidente Associazione"),
    (6, "Consigliere", "Consigliere Associazione"),
    (7, "Socio Sostenitore", "Socio Sostenitore Associazione"),
    (8, "Socio Bandista", "Socio Iscritto all'Associazione"),
]

RUOLI_PERMESSI = {
    2: [
        "utenti:read",
        "utenti:write",
        "ruoli:read",
        "ruoli:write",
        "anagrafica:read",
        "anagrafica:write",
        "contabilita:read",
        "contabilita:write",
        "servizi:read",
        "servizi:write",
        "archivio:read",
        "archivio:write",
        "iscrizioni:read",
        "iscrizioni:write",
    ],
    3: [
        "utenti:read",
        "utenti:write",
        "ruoli:read",
        "anagrafica:read",
        "anagrafica:write",
        "contabilita:read",
        "contabilita:write",
        "servizi:read",
        "servizi:write",
        "archivio:read",
        "archivio:write",
        "iscrizioni:read",
        "iscrizioni:write",
    ],
    4: [
        "utenti:read",
        "utenti:write",
        "ruoli:read",
        "ruoli:write",
        "anagrafica:read",
        "anagrafica:write",
        "contabilita:read",
        "servizi:read",
        "servizi:write",
        "archivio:read",
        "archivio:write",
        "iscrizioni:read",
        "iscrizioni:write",
    ],
    5: [
        "utenti:read",
        "utenti:write",
        "ruoli:read",
        "ruoli:write",
        "anagrafica:read",
        "anagrafica:write",
        "contabilita:read",
        "contabilita:write",
        "servizi:read",
        "servizi:write",
        "archivio:read",
        "archivio:write",
        "iscrizioni:read",
        "iscrizioni:write",
    ],
    6: [
        "utenti:read",
        "ruoli:read",
        "anagrafica:read",
        "contabilita:read",
        "servizi:read",
        "servizi:write",
        "archivio:read",
        "archivio:write",
        "iscrizioni:read",
    ],
    7: [
        "utenti:read",
        "ruoli:read",
        "anagrafica:read",
        "contabilita:read",
        "servizi:read",
        "archivio:read",
        "archivio:write",
        "iscrizioni:read",
    ],
    8: [
        "anagrafica:read",
        "contabilita:read",
        "servizi:read",
        "archivio:read",
        "archivio:write",
        "iscrizioni:read",
    ],
}


def upgrade() -> None:
    bind = op.get_bind()

    for ruolo_id, nome, descrizione in RUOLI:
        bind.execute(
            sa.text(
                """
                INSERT INTO ruoli (id, nome, descrizione, banda_codice)
                VALUES (:id, :nome, :desc, NULL)
                ON CONFLICT (id) DO UPDATE SET
                    nome = EXCLUDED.nome,
                    descrizione = EXCLUDED.descrizione
                """
            ),
            {"id": ruolo_id, "nome": nome, "desc": descrizione},
        )

    for ruolo_id, permessi in RUOLI_PERMESSI.items():
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
    for ruolo_id, _, _ in RUOLI:
        bind.execute(
            sa.text("DELETE FROM ruoli_permessi WHERE ruolo_id = :rid"),
            {"rid": ruolo_id},
        )
        bind.execute(
            sa.text("DELETE FROM ruoli WHERE id = :rid"),
            {"rid": ruolo_id},
        )
