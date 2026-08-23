class SchedaAlunnoVoceNotFoundError(Exception):
    """Nessuna voce con questo id per questa scheda alunno.

    Sollevata anche quando la voce esiste ma appartiene a un'altra scheda:
    l'endpoint è annidato sotto ``/schede-alunno/{scheda_alunno_id}/voci``,
    e un id di voce valido ma fuori scheda non deve distinguersi da un id
    inesistente.
    """

    def __init__(self, voce_id: int) -> None:
        self.voce_id = voce_id
        super().__init__(f"Voce {voce_id} non trovata per questa scheda alunno")


class VoceCatalogoNonCompatibileError(Exception):
    """La voce di catalogo non è utilizzabile per questa scheda: è disattivata
    o appartiene a un tipo corso diverso da quello del corso della scheda.

    422 anziché 404: la voce di catalogo esiste, ma non è valida in questo
    contesto — stesso trattamento di ``PresenzaContainerMismatchError`` in
    ``app.api.v1.presenze`` per le violazioni di coerenza di dominio.
    """

    def __init__(self, voce_catalogo_id: int, tipo_corso_codice: int) -> None:
        self.voce_catalogo_id = voce_catalogo_id
        self.tipo_corso_codice = tipo_corso_codice
        super().__init__(
            f"La voce di catalogo {voce_catalogo_id} non è attiva o non è "
            f"del tipo corso {tipo_corso_codice} di questa scheda"
        )
