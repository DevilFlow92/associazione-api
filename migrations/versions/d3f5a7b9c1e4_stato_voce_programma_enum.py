"""stato voce programma: da VARCHAR a enum DB

Corregge una svista della card precedente: ``stato`` su
``scheda_alunno_voci`` (e ``stato_precedente``/``stato_nuovo`` su
``scheda_alunno_voci_storico``) era stato implementato come ``VARCHAR(20)``
semplice, mentre il pattern già in uso nel progetto per enum persistiti su
colonna è un ``Enum`` SQLAlchemy nativo — vedi ``StatoPresenza``
(``stato_presenza``, migration ``03a9929d4789``) e ``TipoFlussoCassa``
(``tipo_flusso_cassa``, migration ``5b0fd2895d05``).

Le tre colonne condividono lo stesso tipo Postgres ``stato_voce_programma``
(creato una sola volta): sono la stessa enumerazione di dominio
(``StatoVoceProgramma``), non tre enum indipendenti.

Nessun dato reale da migrare: la funzionalità non è ancora in produzione
(``scheda_alunno_voci``/``scheda_alunno_voci_storico`` introdotte da
``9f1e3d5c7b2a``/``b2d4f6a8c0e3`` nello stesso rilascio), quindi la
conversione ``USING`` è diretta senza normalizzazione di valori pregressi.

Revision ID: d3f5a7b9c1e4
Revises: b2d4f6a8c0e3
Create Date: 2026-08-23 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d3f5a7b9c1e4"
down_revision: str | Sequence[str] | None = "b2d4f6a8c0e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

stato_voce_programma = postgresql.ENUM(
    "da_iniziare",
    "in_corso",
    "acquisita",
    name="stato_voce_programma",
)


def upgrade() -> None:
    stato_voce_programma.create(op.get_bind(), checkfirst=True)

    op.execute(
        "ALTER TABLE scheda_alunno_voci ALTER COLUMN stato TYPE "
        "stato_voce_programma USING stato::stato_voce_programma"
    )
    op.execute(
        "ALTER TABLE scheda_alunno_voci_storico ALTER COLUMN stato_precedente "
        "TYPE stato_voce_programma USING stato_precedente::stato_voce_programma"
    )
    op.execute(
        "ALTER TABLE scheda_alunno_voci_storico ALTER COLUMN stato_nuovo TYPE "
        "stato_voce_programma USING stato_nuovo::stato_voce_programma"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE scheda_alunno_voci_storico ALTER COLUMN stato_nuovo "
        "TYPE VARCHAR(20) USING stato_nuovo::text"
    )
    op.execute(
        "ALTER TABLE scheda_alunno_voci_storico ALTER COLUMN stato_precedente "
        "TYPE VARCHAR(20) USING stato_precedente::text"
    )
    op.execute(
        "ALTER TABLE scheda_alunno_voci ALTER COLUMN stato "
        "TYPE VARCHAR(20) USING stato::text"
    )

    stato_voce_programma.drop(op.get_bind(), checkfirst=True)
