"""Autorizzazione *row-level*: chi sta chiedendo, non solo cosa sta chiedendo.

L'RBAC del progetto (``require_permission`` in ``app/api/deps.py``) è puro
resource:action — decide guardando i permessi del principal, mai il contenuto
della riga richiesta. Per la scheda alunno questo non basta: l'alunno non ha
alcun permesso ``corsi:*`` e deve comunque poter leggere **la propria** scheda,
e solo quella.

Il modulo espone funzioni pure (utente + dati della riga → decisione), senza
dipendenze da FastAPI né dalla sessione DB: sono testabili in isolamento e
riusabili dalla card successiva (portale alunno). Il caricamento della riga e
la traduzione in 403 restano a carico di service e router.

Il perimetro di LETTURA e quello di SCRITTURA non sono più simmetrici (lo
erano nella card #175 originale):

- LETTURA — ``livello_accesso_scheda``/``assert_puo_leggere_scheda``: chi ha
  ``corsi:write`` (o superuser) legge QUALSIASI scheda, indipendentemente dal
  corso; altrimenti solo l'alunno proprietario legge la propria (sola
  lettura). Deciso di non restringere anche qui: il testo della card parlava
  solo di "scrivere le schede dei propri corsi", e i router GET
  (``corsi:read``) non passano mai da questo modulo — restringerli avrebbe
  richiesto una card a parte.
- SCRITTURA — ``assert_puo_scrivere_scheda``: non basta più ``corsi:write``
  da solo. Serve anche che la Persona collegata all'utente sia insegnante o
  coordinatore del CORSO SPECIFICO a cui la scheda appartiene
  (``corso.insegnante_persona_id``/``coordinatore_persona_id``, risalito da
  ``scheda → iscrizione_corso → corso``). Il superuser bypassa sempre questa
  restrizione, stesso pattern consolidato di
  ``app.services.permessi_archivio.require_write`` e
  ``app.api.deps.require_permission``. L'alunno proprietario resta escluso
  in ogni caso (non ha mai ``corsi:write``).
"""

from __future__ import annotations

import enum

from app.exceptions.scheda_alunno import AccessoSchedaAlunnoNegatoError
from app.models.corso import Corso
from app.models.utente import Utente

# Permesso che abilita la gestione dei corsi (insegnante/coordinatore/gestione).
PERMESSO_SCRITTURA_CORSI = "corsi:write"


class LivelloAccessoScheda(enum.StrEnum):
    """Esito della valutazione row-level su una singola scheda."""

    COMPLETO = "completo"
    SOLA_LETTURA = "sola_lettura"
    NESSUNO = "nessuno"


def ha_gestione_corsi(utente: Utente) -> bool:
    """True se il principal gestisce i corsi (superuser o ``corsi:write``)."""
    return utente.superuser or PERMESSO_SCRITTURA_CORSI in utente.permessi


def e_alunno_della_scheda(utente: Utente, persona_id_alunno: int) -> bool:
    """True se il principal *è* l'alunno a cui la scheda si riferisce.

    Il confronto richiede un ``persona_id`` valorizzato su entrambi i lati:
    un utente senza Persona collegata (``persona_id`` nullo) non è mai
    l'alunno di nessuna scheda — senza il controllo esplicito su ``None``
    un confronto ``None == None`` lo farebbe passare.
    """
    return utente.persona_id is not None and utente.persona_id == persona_id_alunno


def e_docente_del_corso(utente: Utente, corso: Corso) -> bool:
    """True se il principal *è* insegnante o coordinatore di quel corso.

    Stesso guardrail di ``e_alunno_della_scheda``: un utente senza Persona
    collegata (``persona_id`` nullo) non è mai insegnante/coordinatore di
    nessun corso, anche se ``corso.insegnante_persona_id`` o
    ``coordinatore_persona_id`` fossero a loro volta nulli — evita che
    ``None`` combaci con ``None``.
    """
    if utente.persona_id is None:
        return False
    return utente.persona_id in (
        corso.insegnante_persona_id,
        corso.coordinatore_persona_id,
    )


def livello_accesso_scheda(
    utente: Utente, persona_id_alunno: int
) -> LivelloAccessoScheda:
    """Valuta il livello di accesso in LETTURA del principal alla scheda.

    Non usata per la scrittura: vedi ``assert_puo_scrivere_scheda``, che ha
    un perimetro più stretto (corso specifico) non esprimibile con questo
    stesso enum senza confondere i due significati.
    """
    if ha_gestione_corsi(utente):
        return LivelloAccessoScheda.COMPLETO
    if e_alunno_della_scheda(utente, persona_id_alunno):
        return LivelloAccessoScheda.SOLA_LETTURA
    return LivelloAccessoScheda.NESSUNO


def assert_puo_leggere_scheda(utente: Utente, persona_id_alunno: int) -> None:
    """Impone il diritto di LETTURA sulla scheda; solleva altrimenti."""
    livello = livello_accesso_scheda(utente, persona_id_alunno)
    if livello is LivelloAccessoScheda.NESSUNO:
        raise AccessoSchedaAlunnoNegatoError(
            "La scheda alunno è accessibile solo al personale dei corsi "
            "e all'alunno a cui si riferisce"
        )


def assert_puo_scrivere_scheda(utente: Utente, corso: Corso) -> None:
    """Impone il diritto di SCRITTURA sulla scheda del corso indicato.

    A differenza della lettura, qui ``corsi:write`` da solo non basta più:
    serve anche essere insegnante o coordinatore di QUESTO corso specifico
    (``e_docente_del_corso``). Il superuser bypassa sempre la restrizione,
    controllato per primo — stesso pattern di
    ``permessi_archivio.require_write``. L'alunno proprietario resta escluso
    in ogni caso: la scheda contiene il programma redatto da
    insegnante/coordinatore, l'alunno la legge e basta.
    """
    if utente.superuser:
        return
    if ha_gestione_corsi(utente) and e_docente_del_corso(utente, corso):
        return
    raise AccessoSchedaAlunnoNegatoError(
        f"Modifica della scheda alunno riservata a chi ha "
        f"{PERMESSO_SCRITTURA_CORSI} ed è insegnante o coordinatore di questo corso"
    )
