"""pass 3 — archivio documentale (tipi documento/spartito, stati iscrizione,
remodel documenti & templates, spartiti, iscrizioni)

- Nuovi lookup: tipi_documento, tipi_spartito, stati_iscrizione.
- documenti: rimuove l'enum `tipo` e il legame `socio_id`; aggiunge il FK
  `tipo_documento_codice` (con backfill dai vecchi valori enum).
- templates: ricostruita per referenziare un Documento (drop & recreate →
  i record template file-based esistenti vengono persi).
- ricevute: `servizio_id`/`esterno_id` diventano nullable; aggiunge
  `documento_id`.
- Nuove tabelle: spartiti, iscrizioni.

Revision ID: d4a9c7b1f3e2
Revises: c5f8b1a2e9d3
Create Date: 2026-06-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4a9c7b1f3e2"
down_revision: str | Sequence[str] | None = "c5f8b1a2e9d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # ── Nuovi lookup ─────────────────────────────────────────────────────────
    for tabella in ("tipi_documento", "tipi_spartito", "stati_iscrizione"):
        op.create_table(
            tabella,
            sa.Column("codice", sa.SmallInteger(), autoincrement=False, nullable=False),
            sa.Column("descrizione", sa.String(length=100), nullable=False),
            sa.PrimaryKeyConstraint("codice"),
        )

    # Seed dei tipi documento (incl. i 4 valori legacy) per il backfill sotto.
    op.execute(
        """
        INSERT INTO tipi_documento (codice, descrizione) VALUES
            (1, 'Modulo iscrizione'),
            (2, 'Ricevuta'),
            (3, 'Spartito'),
            (4, 'Comunicazione'),
            (5, 'Rendiconto'),
            (6, 'Altro')
        ON CONFLICT (codice) DO NOTHING
        """
    )

    # ── documenti: tipo enum → tipo_documento_codice (FK) ────────────────────
    op.add_column(
        "documenti",
        sa.Column("tipo_documento_codice", sa.SmallInteger(), nullable=True),
    )
    op.execute(
        """
        UPDATE documenti SET tipo_documento_codice = CASE tipo
            WHEN 'modulo_iscrizione' THEN 1
            WHEN 'ricevuta' THEN 2
            WHEN 'partitura' THEN 3
            WHEN 'altro' THEN 6
            ELSE NULL
        END
        """
    )
    op.create_foreign_key(
        "fk_documenti_tipo_documento_codice",
        "documenti",
        "tipi_documento",
        ["tipo_documento_codice"],
        ["codice"],
    )
    op.drop_column("documenti", "tipo")
    op.drop_column("documenti", "socio_id")

    # ── ricevute: servizio/esterno opzionali + documento_id ──────────────────
    op.alter_column(
        "ricevute", "servizio_id", existing_type=sa.Integer(), nullable=True
    )
    op.alter_column("ricevute", "esterno_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("ricevute", sa.Column("documento_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_ricevute_documento_id",
        "ricevute",
        "documenti",
        ["documento_id"],
        ["id"],
    )

    # ── templates: drop & recreate (referenzia un Documento) ─────────────────
    op.drop_table("templates")
    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("documento_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("descrizione", sa.String(length=500), nullable=True),
        sa.Column("creato_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column("aggiornato_il", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["documento_id"], ["documenti.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── spartiti ─────────────────────────────────────────────────────────────
    op.create_table(
        "spartiti",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo_spartito_codice", sa.SmallInteger(), nullable=False),
        sa.Column("strumento_codice", sa.SmallInteger(), nullable=True),
        sa.Column("documento_id", sa.Integer(), nullable=False),
        sa.Column("scaffale", sa.String(length=50), nullable=True),
        sa.Column("ripiano", sa.String(length=50), nullable=True),
        sa.Column("cartella", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["documento_id"], ["documenti.id"]),
        sa.ForeignKeyConstraint(["strumento_codice"], ["strumenti.codice"]),
        sa.ForeignKeyConstraint(["tipo_spartito_codice"], ["tipi_spartito.codice"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── iscrizioni ───────────────────────────────────────────────────────────
    op.create_table(
        "iscrizioni",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("socio_id", sa.Integer(), nullable=False),
        sa.Column("anno", sa.Integer(), nullable=False),
        sa.Column(
            "quota_partecipazione", sa.Numeric(precision=10, scale=2), nullable=False
        ),
        sa.Column("stato_iscrizione_codice", sa.SmallInteger(), nullable=False),
        sa.Column("documento_id", sa.Integer(), nullable=True),
        sa.Column("ricevuta_id", sa.Integer(), nullable=True),
        sa.Column("data_iscrizione", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["documento_id"], ["documenti.id"]),
        sa.ForeignKeyConstraint(["ricevuta_id"], ["ricevute.id"]),
        sa.ForeignKeyConstraint(["socio_id"], ["soci.id"]),
        sa.ForeignKeyConstraint(
            ["stato_iscrizione_codice"], ["stati_iscrizione.codice"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("socio_id", "anno", name="uq_iscrizione_socio_anno"),
    )


def downgrade() -> None:
    """Downgrade schema.

    Best-effort: i record template file-based originari non sono ripristinabili
    e i valori `documenti.tipo` non vengono ricostruiti dal codice.
    """
    op.drop_table("iscrizioni")
    op.drop_table("spartiti")

    op.drop_table("templates")
    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("descrizione", sa.String(length=500), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("dimensione_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("attivo", sa.Boolean(), nullable=False),
        sa.Column("creato_il", sa.DateTime(timezone=True), nullable=False),
        sa.Column("aggiornato_il", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.drop_constraint("fk_ricevute_documento_id", "ricevute", type_="foreignkey")
    op.drop_column("ricevute", "documento_id")
    op.alter_column(
        "ricevute", "esterno_id", existing_type=sa.Integer(), nullable=False
    )
    op.alter_column(
        "ricevute", "servizio_id", existing_type=sa.Integer(), nullable=False
    )

    op.add_column("documenti", sa.Column("socio_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "documenti_socio_id_fkey", "documenti", "soci", ["socio_id"], ["id"]
    )
    op.add_column("documenti", sa.Column("tipo", sa.String(length=50), nullable=True))
    op.drop_constraint(
        "fk_documenti_tipo_documento_codice", "documenti", type_="foreignkey"
    )
    op.drop_column("documenti", "tipo_documento_codice")

    op.drop_table("stati_iscrizione")
    op.drop_table("tipi_spartito")
    op.drop_table("tipi_documento")
