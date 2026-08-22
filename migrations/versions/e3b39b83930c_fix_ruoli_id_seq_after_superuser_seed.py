"""fix ruoli_id_seq dopo seed superuser con id esplicito

e1f2a3b4c5d6 inserisce il ruolo ``superuser`` con ``id=1`` esplicito, ma
senza avanzare ``ruoli_id_seq``. Su un DB nato da zero la sequence resta a
1 (mai chiamata), quindi il primo INSERT successivo che si affida a
``nextval()`` (il seed del ruolo ``Ospite`` in f1a2b3c4d5e6) rigenera id=1
e fallisce con UniqueViolation su ``ruoli_pkey``.

Questa migration si inserisce subito dopo e1f2a3b4c5d6 nella catena (il
``down_revision`` del suo unico figlio diretto, 4185ab91d4eb, è stato
aggiornato per puntare qui), quindi precede sia le 8 migration intermedie
sia f1a2b3c4d5e6, garantendo che il fix sia in vigore prima del primo
INSERT che usa la sequence (``nextval()`` nel seed del ruolo Ospite). Non
tocca il contenuto/revision id di e1f2a3b4c5d6 né di 4185ab91d4eb, entrambe
già applicate in produzione: per i DB che hanno già superato 4185ab91d4eb
nella loro storia, alembic non rigioca questa revision (è "a monte" della
revision corrente), quindi l'inserimento è innocuo.

ASSUNZIONE DA VERIFICARE MANUALMENTE PRIMA DEL DEPLOY: sul DB locale di
sviluppo, la revision corrente (``alembic_version``) risulta a valle di
4185ab91d4eb — verificato camminando la catena down_revision dalla head
attuale fino alla base. Questo NON è stato verificato contro il DB di
produzione (nessun accesso da questo ambiente): prima di applicare questa
migration in produzione, confermare che ``SELECT version_num FROM
alembic_version`` in produzione corrisponda a una revision a valle di
4185ab91d4eb nella catena (qualunque migration applicata dopo
"add strumento_codice to soci" in poi). Se invece la produzione fosse
ferma esattamente a e1f2a3b4c5d6 (scenario molto improbabile vista la
data di merge), questa migration verrebbe eseguita normalmente comunque,
senza problemi.

Revision ID: e3b39b83930c
Revises: e1f2a3b4c5d6
Create Date: 2026-08-22 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3b39b83930c"
down_revision: str | Sequence[str] | None = "e1f2a3b4c5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Idempotente: usa MAX(id) reale, sicuro sia su DB vuoti (dove la
    # sequence va corretta ora) sia su DB esistenti dove è già allineata.
    op.execute(
        "SELECT setval('ruoli_id_seq', COALESCE((SELECT MAX(id) FROM ruoli), 1))"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # No-op: riportare la sequence a un valore precedente non ha senso
    # (non correggerebbe nulla e rischierebbe di reintrodurre il bug),
    # e non c'è uno stato "prima" significativo da ripristinare.
    pass
