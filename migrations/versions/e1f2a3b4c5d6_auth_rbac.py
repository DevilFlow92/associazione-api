"""autenticazione & RBAC — utenti, ruoli, permessi, sessioni

Introduce il modello di autenticazione su due piani descritto nel README:

- ``utenti``: principal autenticabile, umano (login + sessioni) o service
  account (JWT). Porta ``password_hash`` bcrypt, ``tipo``, ``superuser``.
- ``ruoli`` / ``permessi`` / ``ruoli_permessi`` / ``utenti_ruoli``: modello RBAC
  configurabile per associazione.
- ``sessioni``: sessioni server-side revocabili per gli utenti umani.

Seed: catalogo permessi base, un ruolo globale ``superuser`` e un utente
amministratore di bootstrap. La password dell'admin è letta da
``BOOTSTRAP_ADMIN_PASSWORD`` (default ``changeme`` — DA CAMBIARE in produzione).

Revision ID: e1f2a3b4c5d6
Revises: d4a9c7b1f3e2
Create Date: 2026-06-17 00:00:00.000000

"""

import os
from collections.abc import Sequence

import bcrypt
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: str | Sequence[str] | None = "d4a9c7b1f3e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Catalogo dei permessi atomici dichiarati dall'applicazione, nella forma
# risorsa:azione. La mappatura ai ruoli resta configurabile a runtime.
PERMESSI: list[tuple[str, str]] = [
    ("utenti:read", "Visualizzare utenti"),
    ("utenti:write", "Gestire utenti"),
    ("ruoli:read", "Visualizzare ruoli e permessi"),
    ("ruoli:write", "Gestire ruoli e permessi"),
    ("anagrafica:read", "Visualizzare anagrafica (persone, soci, esterni)"),
    ("anagrafica:write", "Gestire anagrafica"),
    ("contabilita:read", "Visualizzare contabilità"),
    ("contabilita:write", "Gestire contabilità"),
    ("servizi:read", "Visualizzare eventi e ricevute"),
    ("servizi:write", "Gestire eventi e ricevute"),
    ("archivio:read", "Visualizzare archivio documentale e spartiti"),
    ("archivio:write", "Gestire archivio documentale e spartiti"),
]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "permessi",
        sa.Column("codice", sa.String(length=64), nullable=False),
        sa.Column("descrizione", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("codice"),
    )

    op.create_table(
        "ruoli",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=64), nullable=False),
        sa.Column("descrizione", sa.String(length=255), nullable=True),
        sa.Column("banda_codice", sa.SmallInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("banda_codice", "nome", name="uq_ruolo_banda_nome"),
    )

    op.create_table(
        "utenti",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum("UMANO", "SERVIZIO", name="tipo_utente"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("nome_completo", sa.String(length=255), nullable=True),
        sa.Column("attivo", sa.Boolean(), nullable=False),
        sa.Column("superuser", sa.Boolean(), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=True),
        sa.Column("creato_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column("aggiornato_il", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["persona_id"], ["persone.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_utenti_email", "utenti", ["email"], unique=True)

    op.create_table(
        "ruoli_permessi",
        sa.Column("ruolo_id", sa.Integer(), nullable=False),
        sa.Column("permesso_codice", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["permesso_codice"], ["permessi.codice"]),
        sa.ForeignKeyConstraint(["ruolo_id"], ["ruoli.id"]),
        sa.PrimaryKeyConstraint("ruolo_id", "permesso_codice"),
    )

    op.create_table(
        "utenti_ruoli",
        sa.Column("utente_id", sa.Integer(), nullable=False),
        sa.Column("ruolo_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["ruolo_id"], ["ruoli.id"]),
        sa.ForeignKeyConstraint(["utente_id"], ["utenti.id"]),
        sa.PrimaryKeyConstraint("utente_id", "ruolo_id"),
    )

    op.create_table(
        "sessioni",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utente_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("creata_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scade_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocata_il", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["utente_id"], ["utenti.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessioni_utente_id", "sessioni", ["utente_id"])
    op.create_index("ix_sessioni_token_hash", "sessioni", ["token_hash"], unique=True)

    _seed()


def _seed() -> None:
    bind = op.get_bind()

    # Catalogo permessi.
    op.bulk_insert(
        sa.table(
            "permessi",
            sa.column("codice", sa.String),
            sa.column("descrizione", sa.String),
        ),
        [{"codice": c, "descrizione": d} for c, d in PERMESSI],
    )

    # Ruolo globale superuser.
    op.bulk_insert(
        sa.table(
            "ruoli",
            sa.column("id", sa.Integer),
            sa.column("nome", sa.String),
            sa.column("descrizione", sa.String),
            sa.column("banda_codice", sa.SmallInteger),
        ),
        [
            {
                "id": 1,
                "nome": "superuser",
                "descrizione": "Accesso completo (bootstrap)",
                "banda_codice": None,
            }
        ],
    )
    # Il superuser bypassa i permessi nel codice, ma assegniamo comunque tutti i
    # permessi al ruolo così è esplicito e utilizzabile come template.
    op.bulk_insert(
        sa.table(
            "ruoli_permessi",
            sa.column("ruolo_id", sa.Integer),
            sa.column("permesso_codice", sa.String),
        ),
        [{"ruolo_id": 1, "permesso_codice": c} for c, _ in PERMESSI],
    )

    # Utente amministratore di bootstrap.
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "changeme")
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    res = bind.execute(
        sa.text(
            """
            INSERT INTO utenti
                (tipo, email, password_hash, nome_completo, attivo, superuser,
                 creato_il, aggiornato_il)
            VALUES
                ('UMANO', :email, :ph, :nome, true, true, now(), now())
            RETURNING id
            """
        ),
        {
            "email": "admin@cosequences.com",
            "ph": password_hash,
            "nome": "Amministratore",
        },
    )
    admin_id = res.scalar_one()
    bind.execute(
        sa.text("INSERT INTO utenti_ruoli (utente_id, ruolo_id) VALUES (:uid, 1)"),
        {"uid": admin_id},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_sessioni_token_hash", table_name="sessioni")
    op.drop_index("ix_sessioni_utente_id", table_name="sessioni")
    op.drop_table("sessioni")
    op.drop_table("utenti_ruoli")
    op.drop_table("ruoli_permessi")
    op.drop_index("ix_utenti_email", table_name="utenti")
    op.drop_table("utenti")
    op.drop_table("ruoli")
    op.drop_table("permessi")
    sa.Enum(name="tipo_utente").drop(op.get_bind(), checkfirst=True)
