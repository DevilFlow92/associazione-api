class SchedaAlunnoAutovalutazioneNotFoundError(Exception):
    """Nessuna autovalutazione con questo id per questa scheda alunno.

    Sollevata anche quando l'autovalutazione esiste ma appartiene a un'altra
    scheda o è stata scritta da un'altra persona: l'endpoint è annidato sotto
    ``/schede-alunno/me/{iscrizione_corso_id}/autovalutazioni``, stesso
    trattamento già in uso per ``SchedaAlunnoVoceNotFoundError``/
    ``SchedaAlunnoMaterialeNotFoundError``.
    """

    def __init__(self, autovalutazione_id: int) -> None:
        self.autovalutazione_id = autovalutazione_id
        super().__init__(
            f"Autovalutazione {autovalutazione_id} non trovata per questa scheda alunno"
        )
