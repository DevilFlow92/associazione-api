"""ricevute: persona_id generalizzato e tipo_ricevuta

Generalizza ``Ricevuta`` da ``esterno_id`` a ``persona_id``: una ricevuta
legata a un servizio ora può riguardare un compenso pagato a un socio,
oltre che a un esterno come già avveniva (coerente con ``Presenza``, che
referenzia la persona indipendentemente dal ruolo). ``esterno_id`` NON
viene droppato in questa migration: resta per compatibilità con i record
storici, semplicemente non più scritto dall'applicazione da questo punto
in poi. La rimozione è rimandata a una migration futura, dopo aver
validato in produzione il backfill fatto qui.

Aggiunge anche ``tipo_ricevuta`` (PAGAMENTO/RISCOSSIONE) per distinguere un
compenso pagato (uscita) da una riscossione da un committente (entrata).
È nullable: il tipo è determinabile con certezza solo per i record che
avevano già ``esterno_id`` valorizzato (erano sempre compensi pagati a un
esterno per un servizio => PAGAMENTO). Per gli altri record esistenti
(es. le ricevute di quota iscrizione, che non hanno né servizio né
esterno/persona) non c'è modo di dedurre il tipo con certezza dai soli
dati storici, quindi resta NULL piuttosto che indovinare.

Backfill: per ogni ricevuta con ``esterno_id`` valorizzato, ``persona_id``
viene popolato leggendo ``esterni.persona_id`` con un UPDATE...FROM diretto
in SQL (nessun caricamento di oggetti ORM in migration). ``persona_id``
resta nullable perché le ricevute di quota iscrizione non hanno una
persona diretta da backfillare (sono collegate solo dall'iscrizione via
``ricevuta_id``).

Revision ID: d1a5c8f36b2e
Revises: 74e4f7c2a1dc
Create Date: 2026-07-19 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d1a5c8f36b2e"
down_revision: str | Sequence[str] | None = "74e4f7c2a1dc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

tipo_ricevuta_enum = postgresql.ENUM("PAGAMENTO", "RISCOSSIONE", name="tipo_ricevuta")


def upgrade() -> None:
    """Upgrade schema."""
    tipo_ricevuta_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("ricevute", sa.Column("persona_id", sa.Integer(), nullable=True))
    op.add_column(
        "ricevute",
        sa.Column(
            "tipo_ricevuta",
            sa.Enum(
                "PAGAMENTO",
                "RISCOSSIONE",
                name="tipo_ricevuta",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_ricevute_persona_id", "ricevute", "persone", ["persona_id"], ["id"]
    )

    # Backfill persona_id dai record esistenti con esterno_id valorizzato.
    op.execute(
        """
        UPDATE ricevute
        SET persona_id = esterni.persona_id
        FROM esterni
        WHERE ricevute.esterno_id = esterni.id
        """
    )

    # tipo_ricevuta certo solo dove esterno_id era valorizzato: erano
    # sempre compensi pagati a un esterno per un servizio.
    op.execute(
        """
        UPDATE ricevute
        SET tipo_ricevuta = 'PAGAMENTO'
        WHERE esterno_id IS NOT NULL
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_ricevute_persona_id", "ricevute", type_="foreignkey")
    op.drop_column("ricevute", "tipo_ricevuta")
    op.drop_column("ricevute", "persona_id")
    tipo_ricevuta_enum.drop(op.get_bind(), checkfirst=True)
