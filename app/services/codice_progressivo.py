from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

WIDTH = 5
MAX_TENTATIVI = 5

# Chiavi arbitrarie e distinte per entità, usate come primo argomento di
# pg_advisory_xact_lock insieme a banda_codice: individuano lo spazio di
# codici da serializzare (es. i codice_socio della banda 3 sono uno spazio
# diverso dai codice_esterno della banda 3).
LOCK_KEY_SOCIO = 1
LOCK_KEY_ESTERNO = 2
LOCK_KEY_ALLIEVO = 3


def next_codice_progressivo(codici_esistenti: Iterable[str], width: int = WIDTH) -> str:
    """Primo numero libero (a partire da 1) tra i codici esistenti della
    banda, colmando eventuali buchi lasciati da cancellazioni (se esistono
    1, 2, 4, ritorna 3), formattato come stringa zero-padded a `width`
    cifre.

    I codici non puramente numerici vengono ignorati nella scansione: non
    fanno parte della sequenza progressiva (possono esistere solo come
    valori legacy inseriti manualmente prima dell'introduzione di questa
    generazione server-side).
    """
    usati = {int(codice) for codice in codici_esistenti if codice.isdigit()}
    numero = 1
    while numero in usati:
        numero += 1
    return str(numero).zfill(width)


async def lock_banda(db: AsyncSession, entita_key: int, banda_codice: int) -> None:
    """Serializza, per la durata della transazione corrente, le operazioni
    che assegnano un codice progressivo a una data banda (creazioni e
    correzioni manuali via PATCH), così due richieste concorrenti sulla
    stessa banda non possano mai calcolare/assegnare lo stesso codice.

    Perché un advisory lock e non un vincolo UNIQUE(banda_codice, codice_*)
    reale: banda_codice non è una colonna di soci/esterni/allievi, deriva
    solo da persona_id → persona.banda_codice (commit 6adc79b, "banda
    deriva da persona, rimosso banda_codice da soci") — una scelta
    deliberata per evitare quel dato ridondante. Un vincolo UNIQUE composito
    non è esprimibile in Postgres su colonne di tabelle diverse, quindi
    imporlo richiederebbe denormalizzare banda_codice su queste tre tabelle,
    contraddicendo quella decisione. Si è scelto invece questo lock,
    accettando un presupposto preciso: **nessuna scrittura su codice_socio /
    codice_esterno / codice_allievo deve mai bypassare il service layer**
    (incluso in scenari futuri come uno script di import massivo di
    anagrafiche legacy, che dovrà passare dalle API esistenti — anche in
    batch — e non da query dirette sul DB). Se questo presupposto dovesse
    cambiare, tornerà necessario denormalizzare banda_codice e introdurre un
    vincolo UNIQUE reale.

    No-op quando il dialetto non è PostgreSQL: pg_advisory_xact_lock non
    esiste altrove (es. SQLite, usato dalla test suite), e lì la suite non
    esercita comunque scritture concorrenti reali sulla stessa connessione.
    """
    bind = db.get_bind()
    if bind.dialect.name != "postgresql":
        return
    await db.execute(
        text("SELECT pg_advisory_xact_lock(:entita_key, :banda_codice)"),
        {"entita_key": entita_key, "banda_codice": banda_codice},
    )
