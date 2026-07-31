"""schede alunno — primo controllo di autorizzazione row-level

Quinta card della Fase 3 del backlog Attività. Introduce ``schede_alunno``:
la scheda personale dell'alunno iscritto a un corso, con il programma da
seguire redatto da insegnante/coordinatore.

``iscrizione_corso_id`` è UNIQUE: una scheda per iscrizione. Una persona
re-iscritta allo stesso corso (ammesso dal dominio, vedi ``iscrizioni_corso``)
ottiene una scheda distinta per ciascuna iscrizione.

``aggiornato_da_persona_id`` (nullable) è l'audit di chi ha scritto l'ultimo
aggiornamento: valorizzato dal service con la Persona collegata all'utente
autenticato, non dal payload. Nullable perché ``utenti.persona_id`` è a sua
volta opzionale (un utente di gestione può non essere in anagrafica).

Nessun nuovo permesso: la card riusa ``corsi:read``/``corsi:write``, già
seedati e assegnati ai ruoli di gestione dalla migration f7a2c9e4b6d1. Il
diritto dell'alunno a leggere la propria scheda NON è un permesso RBAC — è un
controllo row-level a runtime (``app/services/rbac_row_level.py``) che
confronta ``utenti.persona_id`` con ``iscrizioni_corso.persona_id``: un
permesso in tabella non potrebbe esprimere "solo la propria".

Revision ID: b8e4d1c6f0a3
Revises: a1c3e5f7b9d2
Create Date: 2026-07-31 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8e4d1c6f0a3"
down_revision: str | Sequence[str] | None = "a1c3e5f7b9d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "schede_alunno",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("iscrizione_corso_id", sa.Integer(), nullable=False),
        sa.Column("programma", sa.Text(), nullable=True),
        sa.Column("aggiornato_da_persona_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["iscrizione_corso_id"], ["iscrizioni_corso.id"]),
        sa.ForeignKeyConstraint(["aggiornato_da_persona_id"], ["persone.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("iscrizione_corso_id", name="uq_schede_alunno_iscrizione"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("schede_alunno")
