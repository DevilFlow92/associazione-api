"""tabelle dimensione — permessi lookup:read/write

Introduce il permesso condiviso ``lookup:read``/``lookup:write`` per le
tabelle dimensione (stati, regioni, province, comuni, strumenti,
tipi-indirizzo, ruoli-contatto, ruoli-banda, tipi-documento, tipi-spartito,
stati-iscrizione, tipi-corso, bande), oggi prive di un gruppo di permesso
dedicato — card #194 (audit e enforcement RBAC uniforme).

Questi dati di lookup sono letti da dropdown usati in praticamente ogni
pagina dell'app, anche da ruoli a basso privilegio (Consigliere, Socio
Sostenitore, Socio Bandista, Ospite): ``lookup:read`` viene quindi assegnato
a tutti i ruoli esistenti, incluso Ospite. ``lookup:write`` resta riservato
ai ruoli di gestione (1 superuser, 2 Presidente, 3 Tesoriere, 4 Segretario,
5 Vice Presidente), stesso schema già in uso per ``templates:write`` e
``corsi:write``.

Revision ID: d5d0a91ceee4
Revises: f7a2c9e4b6d1
Create Date: 2026-07-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d5d0a91ceee4"
down_revision: str | Sequence[str] | None = "f7a2c9e4b6d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Ruoli fissi (id noto) che ricevono lookup:read + lookup:write.
LOOKUP_WRITE_RUOLI = [1, 2, 3, 4, 5]

# Ruoli fissi (id noto) che ricevono solo lookup:read.
LOOKUP_READ_ONLY_RUOLI = [6, 7, 8]


def upgrade() -> None:
    bind = op.get_bind()

    op.execute(
        """
        INSERT INTO permessi (codice, descrizione) VALUES
            ('lookup:read',  'Visualizzare le tabelle dimensione'),
            ('lookup:write', 'Gestire le tabelle dimensione')
        ON CONFLICT DO NOTHING
        """
    )

    for ruolo_id in LOOKUP_WRITE_RUOLI:
        for codice in ("lookup:read", "lookup:write"):
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

    for ruolo_id in LOOKUP_READ_ONLY_RUOLI:
        bind.execute(
            sa.text(
                """
                INSERT INTO ruoli_permessi (ruolo_id, permesso_codice)
                VALUES (:rid, 'lookup:read')
                ON CONFLICT DO NOTHING
                """
            ),
            {"rid": ruolo_id},
        )

    # Ruolo Ospite: id dinamico (globale, banda_codice NULL), come in
    # f1a2b3c4d5e6_ospite_role_and_password_reset_tokens.
    ospite_id = bind.execute(
        sa.text("SELECT id FROM ruoli WHERE nome = 'Ospite' AND banda_codice IS NULL")
    ).scalar_one_or_none()
    if ospite_id:
        bind.execute(
            sa.text(
                """
                INSERT INTO ruoli_permessi (ruolo_id, permesso_codice)
                VALUES (:rid, 'lookup:read')
                ON CONFLICT DO NOTHING
                """
            ),
            {"rid": ospite_id},
        )


def downgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            "DELETE FROM ruoli_permessi WHERE permesso_codice IN "
            "('lookup:read', 'lookup:write')"
        )
    )

    op.execute(
        """
        DELETE FROM permessi WHERE codice IN (
            'lookup:read',
            'lookup:write'
        )
        """
    )
