"""pagamenti corso — auto-posting su FlussoCassa

Quarta card della Fase 3 del backlog Attività. Introduce il pagamento di
una quota corso da parte della Persona iscritta (``IscrizioneCorso``, card
precedente), con auto-posting su ``FlussoCassa`` sul pattern già esistente
AUTO_ISCRIZIONE (quota annuale socio) — non sul pattern Ricevuta-Servizio,
scartato in una card precedente perché privo di una configurazione
contabile chiara.

Decisioni contabili confermate esplicitamente con l'utente prima di questa
migration (non assunte):
- Nuova voce_contabilita dedicata alle rette corsi, distinta da quella delle
  quote associative (``voce_contabilita_quote_id`` è specifica per le quote
  annuali socio, accoppiata a ``quota_annuale_attesa``; riusarla avrebbe
  mescolato due categorie di entrata diverse nel rendiconto). Aggiunto
  ``voce_contabilita_corsi_id`` a ``configurazioni_banda_anno``, stesso
  pattern nullable di ``voce_contabilita_quote_id``.
- L'anno usato per cercare la ``ConfigurazioneBandaAnno`` è quello del
  Corso (``corso.anno``), non l'anno solare del pagamento.
- ``natura_flusso`` hardcoded a "Banca", stessa semplificazione già accettata
  da AUTO_ISCRIZIONE.
- Nuovo valore enum dedicato ``AUTO_PAGAMENTO_CORSO`` (non riuso di
  AUTO_ISCRIZIONE): mantiene la corrispondenza 1:1 tipo↔entità di origine
  già stabilita dal design esistente (``iscrizione_id`` è una FK dedicata,
  non generica/polimorfica — un pagamento corso richiede allo stesso modo
  una FK dedicata ``pagamento_corso_id`` su ``flussi_cassa``).

``PagamentoCorso.ricevuta_id`` è nullable per simmetria con
``Iscrizione.ricevuta_id`` ma in pratica sempre valorizzato dal service:
a differenza di AUTO_ISCRIZIONE (che non genera mai una Ricevuta
automaticamente), qui la Ricevuta RISCOSSIONE viene creata insieme al
pagamento e viene eliminata a cascata insieme ad esso (nessun proprietario
esterno della riga).

Revision ID: a1c3e5f7b9d2
Revises: 1be8bc2638ab
Create Date: 2026-07-30 22:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1c3e5f7b9d2"
down_revision: str | Sequence[str] | None = "1be8bc2638ab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TIPO_FLUSSO_CASSA_SENZA_PAGAMENTO_CORSO = (
    "MOVIMENTO",
    "SALDO_INIZIALE",
    "TRASFERIMENTO_USCITA",
    "TRASFERIMENTO_ENTRATA",
    "AUTO_ISCRIZIONE",
)


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "configurazioni_banda_anno",
        sa.Column("voce_contabilita_corsi_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_cfg_banda_anno_voce_contabilita_corsi_id",
        "configurazioni_banda_anno",
        "voci_contabilita",
        ["voce_contabilita_corsi_id"],
        ["id"],
    )

    op.create_table(
        "pagamenti_corso",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("iscrizione_corso_id", sa.Integer(), nullable=False),
        sa.Column("data_pagamento", sa.Date(), nullable=False),
        sa.Column("importo", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("ricevuta_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["iscrizione_corso_id"], ["iscrizioni_corso.id"]),
        sa.ForeignKeyConstraint(["ricevuta_id"], ["ricevute.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        "ALTER TYPE tipo_flusso_cassa ADD VALUE IF NOT EXISTS 'AUTO_PAGAMENTO_CORSO'"
    )

    op.add_column(
        "flussi_cassa",
        sa.Column("pagamento_corso_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_flussi_cassa_pagamento_corso_id",
        "flussi_cassa",
        "pagamenti_corso",
        ["pagamento_corso_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_flussi_cassa_pagamento_corso_id", "flussi_cassa", type_="foreignkey"
    )
    op.drop_column("flussi_cassa", "pagamento_corso_id")

    # Postgres non supporta ALTER TYPE ... DROP VALUE: si ricrea l'enum senza
    # AUTO_PAGAMENTO_CORSO e si riporta la colonna al tipo originale. Fallisce
    # (intenzionalmente) se esistono righe con tipo=AUTO_PAGAMENTO_CORSO, dato
    # che non sarebbero rappresentabili nell'enum precedente.
    op.execute("ALTER TABLE flussi_cassa ALTER COLUMN tipo DROP DEFAULT")
    op.execute(
        "ALTER TABLE flussi_cassa ALTER COLUMN tipo TYPE varchar USING tipo::text"
    )
    op.execute("DROP TYPE tipo_flusso_cassa")
    postgresql.ENUM(
        *_TIPO_FLUSSO_CASSA_SENZA_PAGAMENTO_CORSO, name="tipo_flusso_cassa"
    ).create(op.get_bind())
    op.execute(
        "ALTER TABLE flussi_cassa ALTER COLUMN tipo TYPE tipo_flusso_cassa "
        "USING tipo::tipo_flusso_cassa"
    )
    op.execute("ALTER TABLE flussi_cassa ALTER COLUMN tipo SET DEFAULT 'MOVIMENTO'")

    op.drop_table("pagamenti_corso")

    op.drop_constraint(
        "fk_cfg_banda_anno_voce_contabilita_corsi_id",
        "configurazioni_banda_anno",
        type_="foreignkey",
    )
    op.drop_column("configurazioni_banda_anno", "voce_contabilita_corsi_id")
