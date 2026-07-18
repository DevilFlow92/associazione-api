"""archivio — macro-sezione Template Images

Aggiunge la macro-sezione "Template Images", riutilizzando il permesso
``templates:read``/``templates:write`` già esistente (introdotto dalla
migrazione ``54cecb82dfc0`` per la modulistica) invece di crearne uno
nuovo dedicato.

Viene posizionata in cima al menù: le quattro macro-sezioni esistenti
(``ordine`` 1-4) vengono spostate di una posizione (2-5) e "Template
Images" occupa ``ordine=1``. Lo shift è idempotente (basato su un
UPDATE condizionale che confronta il valore corrente, non su
un'assunzione "gira una volta sola") cosi' come l'INSERT (ON CONFLICT
DO NOTHING), sul modello della migrazione ``a9b1c3d5e7f2``.

Un Documento non ha mai una FK diretta verso MacroSezione (passa sempre,
se categorizzato, da una SottoCartella - vedi ``b1d3e5f7a9c2``): viene
quindi creata anche una sotto-cartella di default "Immagini modulistica"
cosi' la sezione e' immediatamente utilizzabile.

Revision ID: c4d6e8f0a1b3
Revises: 8b833e91a3b6
Create Date: 2026-07-18 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d6e8f0a1b3"
down_revision: str | Sequence[str] | None = "8b833e91a3b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NUOVO_CODICE = 5
NUOVO_ORDINE = 1


def upgrade() -> None:
    """Upgrade schema."""
    # Sposta le quattro macro-sezioni esistenti (ordine 1-4) di una
    # posizione, per far spazio a "Template Images" in cima al menù.
    # Condizionato su ordine < NUOVO_ORDINE + 4 cosi' un rerun (o un
    # eventuale downgrade/upgrade successivo) non le sposta ulteriormente.
    op.execute(
        f"""
        UPDATE macro_sezioni
        SET ordine = ordine + 1
        WHERE codice != {NUOVO_CODICE} AND ordine < 4
        """
    )

    op.execute(
        f"""
        INSERT INTO macro_sezioni (codice, nome, permesso_prefisso, ordine) VALUES
            ({NUOVO_CODICE}, 'Template Images', 'templates', {NUOVO_ORDINE})
        ON CONFLICT (codice) DO NOTHING
        """
    )

    op.execute(
        f"""
        INSERT INTO sotto_cartelle (nome, macro_sezione_codice)
        SELECT 'Immagini modulistica', {NUOVO_CODICE}
        WHERE NOT EXISTS (
            SELECT 1 FROM sotto_cartelle
            WHERE nome = 'Immagini modulistica'
              AND macro_sezione_codice = {NUOVO_CODICE}
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        f"""
        DELETE FROM sotto_cartelle
        WHERE nome = 'Immagini modulistica' AND macro_sezione_codice = {NUOVO_CODICE}
        """
    )
    op.execute(f"DELETE FROM macro_sezioni WHERE codice = {NUOVO_CODICE}")
    op.execute(
        """
        UPDATE macro_sezioni
        SET ordine = ordine - 1
        WHERE ordine > 1
        """
    )
