"""apply domain model — anagrafica (persone, soci, esterni, lookups)

Sostituisce il modello piatto soci/iscrizioni con il dominio dell'associazione:
tabelle dimensione (lookup), anagrafica persone e relative entità.

NB: pensata per PostgreSQL. Presuppone una tabella ``soci`` vuota (il vecchio
schema piatto non è compatibile con il nuovo).

Revision ID: b7c1d9e2f3a4
Revises: c3f0b0575da1
Create Date: 2026-06-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c1d9e2f3a4"
down_revision: str | Sequence[str] | None = "c3f0b0575da1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _lookup_columns() -> list[sa.Column]:
    return [
        sa.Column("codice", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("descrizione", sa.String(length=100), nullable=False),
    ]


def upgrade() -> None:
    """Upgrade schema."""
    # ── Rimozione del vecchio modello piatto ─────────────────────────────────
    op.drop_table("iscrizioni")
    op.drop_constraint("documenti_socio_id_fkey", "documenti", type_="foreignkey")
    op.drop_table("soci")

    # ── Tabelle dimensione (D_*) ─────────────────────────────────────────────
    op.create_table(
        "stati",
        *_lookup_columns(),
        sa.PrimaryKeyConstraint("codice"),
    )
    op.create_table(
        "regioni",
        *_lookup_columns(),
        sa.Column("stato_codice", sa.SmallInteger(), nullable=True),
        sa.ForeignKeyConstraint(["stato_codice"], ["stati.codice"]),
        sa.PrimaryKeyConstraint("codice"),
    )
    op.create_table(
        "province",
        *_lookup_columns(),
        sa.Column("sigla", sa.String(length=5), nullable=True),
        sa.Column("regione_codice", sa.SmallInteger(), nullable=True),
        sa.ForeignKeyConstraint(["regione_codice"], ["regioni.codice"]),
        sa.PrimaryKeyConstraint("codice"),
    )
    op.create_table(
        "comuni",
        *_lookup_columns(),
        sa.Column("codice_catastale", sa.String(length=6), nullable=True),
        sa.Column("provincia_codice", sa.SmallInteger(), nullable=True),
        sa.ForeignKeyConstraint(["provincia_codice"], ["province.codice"]),
        sa.PrimaryKeyConstraint("codice"),
    )
    op.create_table("strumenti", *_lookup_columns(), sa.PrimaryKeyConstraint("codice"))
    op.create_table(
        "tipi_indirizzo", *_lookup_columns(), sa.PrimaryKeyConstraint("codice")
    )
    op.create_table("bande", *_lookup_columns(), sa.PrimaryKeyConstraint("codice"))
    op.create_table(
        "ruoli_contatto", *_lookup_columns(), sa.PrimaryKeyConstraint("codice")
    )
    op.create_table(
        "ruoli_banda", *_lookup_columns(), sa.PrimaryKeyConstraint("codice")
    )

    # ── Anagrafica (entità core) ─────────────────────────────────────────────
    op.create_table(
        "indirizzi",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo_indirizzo_codice", sa.SmallInteger(), nullable=False),
        sa.Column("prima_riga", sa.String(length=255), nullable=True),
        sa.Column("seconda_riga", sa.String(length=255), nullable=True),
        sa.Column("comune_codice", sa.SmallInteger(), nullable=True),
        sa.Column("cap", sa.String(length=5), nullable=True),
        sa.Column("numero_civico", sa.String(length=10), nullable=True),
        sa.Column("interno", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["comune_codice"], ["comuni.codice"]),
        sa.ForeignKeyConstraint(["tipo_indirizzo_codice"], ["tipi_indirizzo.codice"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "persone",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("banda_codice", sa.SmallInteger(), nullable=False),
        sa.Column("cognome", sa.String(length=255), nullable=True),
        sa.Column("nome", sa.String(length=255), nullable=True),
        sa.Column("ragione_sociale", sa.String(length=255), nullable=True),
        sa.Column("comune_nascita_codice", sa.SmallInteger(), nullable=True),
        sa.Column("data_nascita", sa.Date(), nullable=True),
        sa.Column("codice_fiscale", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["banda_codice"], ["bande.codice"]),
        sa.ForeignKeyConstraint(["comune_nascita_codice"], ["comuni.codice"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "contatti",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ruolo_contatto_codice", sa.SmallInteger(), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("telefono", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["persona_id"], ["persone.id"]),
        sa.ForeignKeyConstraint(["ruolo_contatto_codice"], ["ruoli_contatto.codice"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "soci",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codice_socio", sa.String(length=5), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.Column("banda_codice", sa.SmallInteger(), nullable=False),
        sa.Column("ruolo_banda_codice", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(["banda_codice"], ["bande.codice"]),
        sa.ForeignKeyConstraint(["persona_id"], ["persone.id"]),
        sa.ForeignKeyConstraint(["ruolo_banda_codice"], ["ruoli_banda.codice"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "esterni",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codice_esterno", sa.String(length=5), nullable=False),
        sa.Column("strumento_codice", sa.SmallInteger(), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["persona_id"], ["persone.id"]),
        sa.ForeignKeyConstraint(["strumento_codice"], ["strumenti.codice"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "persone_indirizzi",
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.Column("indirizzo_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["indirizzo_id"], ["indirizzi.id"]),
        sa.ForeignKeyConstraint(["persona_id"], ["persone.id"]),
        sa.PrimaryKeyConstraint("persona_id", "indirizzo_id"),
    )

    # ── Riaggancia il repository documentale al nuovo soci ───────────────────
    op.create_foreign_key(
        "documenti_socio_id_fkey", "documenti", "soci", ["socio_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema — ripristina il vecchio modello piatto."""
    op.drop_constraint("documenti_socio_id_fkey", "documenti", type_="foreignkey")

    op.drop_table("persone_indirizzi")
    op.drop_table("esterni")
    op.drop_table("soci")
    op.drop_table("contatti")
    op.drop_table("persone")
    op.drop_table("indirizzi")
    op.drop_table("ruoli_banda")
    op.drop_table("ruoli_contatto")
    op.drop_table("bande")
    op.drop_table("tipi_indirizzo")
    op.drop_table("strumenti")
    op.drop_table("comuni")
    op.drop_table("province")
    op.drop_table("regioni")
    op.drop_table("stati")

    # Vecchia tabella soci (modello piatto) + iscrizioni.
    op.create_table(
        "soci",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("cognome", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("telefono", sa.String(length=20), nullable=True),
        sa.Column("data_nascita", sa.Date(), nullable=True),
        sa.Column("strumento", sa.String(length=100), nullable=True),
        sa.Column("stato", sa.String(length=20), nullable=False),
        sa.Column("deleted_at", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "iscrizioni",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("socio_id", sa.Integer(), nullable=False),
        sa.Column("anno", sa.Integer(), nullable=False),
        sa.Column("quota_dovuta", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quota_pagata", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("stato_pagamento", sa.String(length=20), nullable=False),
        sa.Column("data_iscrizione", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["socio_id"], ["soci.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_foreign_key(
        "documenti_socio_id_fkey", "documenti", "soci", ["socio_id"], ["id"]
    )
