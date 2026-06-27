"""Ospite role seed + password_reset_tokens table

Introduce:

- la tabella ``password_reset_tokens`` per il reset password via email (token
  monouso, di cui si conserva solo l'hash);
- il ruolo globale ``Ospite`` (banda_codice NULL) usato dall'auto-registrazione,
  con permessi di sola lettura su anagrafica, servizi, iscrizioni e archivio
  (esclusi contabilità e amministrazione).

Revision ID: f1a2b3c4d5e6
Revises: 7a8b9c0d1e2f
Create Date: 2026-06-27 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "7a8b9c0d1e2f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Permessi del ruolo Ospite: read su tutto tranne contabilità e admin.
OSPITE_PERMESSI = [
    "anagrafica:read",
    "servizi:read",
    "iscrizioni:read",
    "archivio:read",
]


def upgrade() -> None:
    # ── Tabella token reset password ─────────────────────────────────────────
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utente_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("scade_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usato_il", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["utente_id"], ["utenti.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )

    # ── Seed ruolo Ospite (globale, banda_codice NULL) ───────────────────────
    bind = op.get_bind()
    # Inserisce il ruolo solo se non già presente (idempotente al re-run).
    bind.execute(
        sa.text(
            """
            INSERT INTO ruoli (nome, descrizione, banda_codice)
            SELECT 'Ospite', 'Accesso in sola lettura (auto-registrazione)', NULL
            WHERE NOT EXISTS (
                SELECT 1 FROM ruoli
                WHERE nome = 'Ospite' AND banda_codice IS NULL
            )
            """
        )
    )
    ospite_id = bind.execute(
        sa.text("SELECT id FROM ruoli WHERE nome = 'Ospite' AND banda_codice IS NULL")
    ).scalar_one()

    for codice in OSPITE_PERMESSI:
        bind.execute(
            sa.text(
                """
                INSERT INTO ruoli_permessi (ruolo_id, permesso_codice)
                VALUES (:rid, :cod)
                ON CONFLICT DO NOTHING
                """
            ),
            {"rid": ospite_id, "cod": codice},
        )


def downgrade() -> None:
    bind = op.get_bind()
    ospite_id = bind.execute(
        sa.text("SELECT id FROM ruoli WHERE nome = 'Ospite' AND banda_codice IS NULL")
    ).scalar_one_or_none()
    if ospite_id:
        bind.execute(
            sa.text("DELETE FROM ruoli_permessi WHERE ruolo_id = :rid"),
            {"rid": ospite_id},
        )
        bind.execute(
            sa.text("DELETE FROM ruoli WHERE id = :rid"),
            {"rid": ospite_id},
        )
    op.drop_index(
        "ix_password_reset_tokens_token_hash", table_name="password_reset_tokens"
    )
    op.drop_table("password_reset_tokens")
