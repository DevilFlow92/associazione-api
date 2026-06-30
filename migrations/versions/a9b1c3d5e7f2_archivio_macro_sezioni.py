"""archivio — struttura a due livelli: macro-sezioni e sotto-cartelle

Introduce la struttura a due livelli dell'archivio documentale:

- ``macro_sezioni``: sezioni fisse seed-ate (Certificazioni Uniche,
  Verbali e Libro Soci, Concorsi e Bandi, Documenti Amministrativi).
  Non sono modificabili a runtime. Ogni sezione porta un
  ``permesso_prefisso`` usato per costruire le coppie RBAC
  ``{prefisso}:read`` / ``{prefisso}:write``, più granulari rispetto
  al generico ``archivio:read/write`` già esistente (che rimane
  invariato — la sua deprecazione è fuori scope).
- ``sotto_cartelle``: cartelle personalizzabili dall'utente all'interno
  di una macro-sezione. Vengono eliminate in CASCADE quando la
  macro-sezione genitrice viene rimossa.

Seed: quattro macro-sezioni fisse e gli otto permessi atomici
corrispondenti (una coppia read/write per sezione).

Revision ID: a9b1c3d5e7f2
Revises: 8acd193111ab
Create Date: 2026-06-30 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9b1c3d5e7f2"
down_revision: str | Sequence[str] | None = "8acd193111ab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Permessi atomici introdotti da questa migrazione.
# archivio:read/write NON vengono toccati — restano invariati.
NUOVI_PERMESSI: list[tuple[str, str]] = [
    ("certificazioni:read", "Visualizzare Certificazioni Uniche"),
    ("certificazioni:write", "Gestire Certificazioni Uniche"),
    ("verbali:read", "Visualizzare Verbali e Libro Soci"),
    ("verbali:write", "Gestire Verbali e Libro Soci"),
    ("concorsi:read", "Visualizzare Concorsi e Bandi"),
    ("concorsi:write", "Gestire Concorsi e Bandi"),
    ("documenti_admin:read", "Visualizzare Documenti Amministrativi"),
    ("documenti_admin:write", "Gestire Documenti Amministrativi"),
]


def upgrade() -> None:
    """Upgrade schema."""
    # ── macro_sezioni ─────────────────────────────────────────────────────────
    op.create_table(
        "macro_sezioni",
        sa.Column("codice", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("permesso_prefisso", sa.String(length=32), nullable=False),
        sa.Column("ordine", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("codice"),
    )

    # ── sotto_cartelle ────────────────────────────────────────────────────────
    op.create_table(
        "sotto_cartelle",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("macro_sezione_codice", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["macro_sezione_codice"],
            ["macro_sezioni.codice"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    _seed()


def _seed() -> None:
    op.execute(
        """
        INSERT INTO macro_sezioni (codice, nome, permesso_prefisso, ordine) VALUES
            (1, 'Certificazioni Uniche', 'certificazioni', 1),
            (2, 'Verbali e Libro Soci', 'verbali', 2),
            (3, 'Concorsi e Bandi', 'concorsi', 3),
            (4, 'Documenti Amministrativi', 'documenti_admin', 4)
        ON CONFLICT (codice) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO permessi (codice, descrizione) VALUES
            ('certificazioni:read',   'Visualizzare Certificazioni Uniche'),
            ('certificazioni:write',  'Gestire Certificazioni Uniche'),
            ('verbali:read',           'Visualizzare Verbali e Libro Soci'),
            ('verbali:write',          'Gestire Verbali e Libro Soci'),
            ('concorsi:read',          'Visualizzare Concorsi e Bandi'),
            ('concorsi:write',         'Gestire Concorsi e Bandi'),
            ('documenti_admin:read',   'Visualizzare Documenti Amministrativi'),
            ('documenti_admin:write',  'Gestire Documenti Amministrativi')
        ON CONFLICT (codice) DO NOTHING
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Rimuove solo i permessi introdotti da questa migrazione;
    # archivio:read/write non vengono toccati.
    op.execute(
        """
        DELETE FROM permessi WHERE codice IN (
            'certificazioni:read',
            'certificazioni:write',
            'verbali:read',
            'verbali:write',
            'concorsi:read',
            'concorsi:write',
            'documenti_admin:read',
            'documenti_admin:write'
        )
        """
    )

    op.drop_table("sotto_cartelle")
    op.drop_table("macro_sezioni")
