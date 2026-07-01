"""nome_parti — FK opzionale verso documenti (audio)

Aggiunge a ``nome_parti`` la colonna ``documento_audio_id`` (Integer,
nullable, FK → documenti.id, ondelete=SET NULL).

Relazione: una ``NomeParte`` PUÒ essere collegata a un file audio (mp3,
mp4, ecc.) archiviato tramite il layer Documento/Storage già esistente.
Questo collegamento è ortogonale a ``url_riferimento`` (link esterno,
es. YouTube o Spotify): entrambi possono coesistere sulla stessa
composizione — ``url_riferimento`` punta a una risorsa esterna,
``documento_audio_id`` punta a un file caricato internamente nel sistema.
L'eliminazione del documento audio orfana il riferimento (SET NULL) senza
cancellare la composizione.

Revision ID: f3b5d7e9a1c4
Revises: e3c1a7f5b9d2
Create Date: 2026-07-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3b5d7e9a1c4"
down_revision: str | Sequence[str] | None = "e3c1a7f5b9d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "nome_parti",
        sa.Column("documento_audio_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_nome_parti_documento_audio_id",
        "nome_parti",
        "documenti",
        ["documento_audio_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_nome_parti_documento_audio_id",
        "nome_parti",
        type_="foreignkey",
    )
    op.drop_column("nome_parti", "documento_audio_id")
